/**
 * test_logic.js
 * -----------------------------------------------------------------------------
 * Exercises the pure server-side logic in Config.gs and Code.gs (validation,
 * duplicate matching, confirmation codes, the RSVP deadline) outside of Google,
 * with the Apps Script services stubbed out.
 *
 *     node tools/test_logic.js
 */

const fs = require('fs'), vm = require('vm'), path = require('path');
const SRC = path.join(__dirname, '..', 'apps-script');

// Minimal stubs for the Apps Script services the pure logic touches.
const ctx = {
  console,
  Utilities: {
    formatDate(d, tz, fmt) { return d.toISOString().slice(0, 10); }
  },
  Math, Date, String, Number, parseInt, isNaN, JSON, RegExp, Array, Object
};
vm.createContext(ctx);
for (const f of ['Config', 'Code']) {
  vm.runInContext(fs.readFileSync(path.join(SRC, `${f}.gs`), 'utf8'), ctx, { filename: f + '.gs' });
}

let pass = 0, fail = 0;
const check = (label, got, want) => {
  const ok = JSON.stringify(got) === JSON.stringify(want);
  ok ? pass++ : fail++;
  console.log(`${ok ? 'PASS' : 'FAIL'}  ${label}${ok ? '' : `\n      got  ${JSON.stringify(got)}\n      want ${JSON.stringify(want)}`}`);
};

const V = p => ctx.validate_(p);

// --- validation ------------------------------------------------------------
check('empty name rejected',        V({name:'', attending:'yes'}).field, 'name');
check('one-char name rejected',     V({name:'A', attending:'yes'}).field, 'name');
check('81-char name rejected',      V({name:'x'.repeat(81), attending:'yes'}).field, 'name');
check('missing attendance rejected',V({name:'Juan Cruz'}).field, 'attending');
check('bogus attendance rejected',  V({name:'Juan Cruz', attending:'maybe'}).field, 'attending');
check('party size 0 rejected',      V({name:'Juan Cruz', attending:'yes', partySize:'0'}).field, 'partySize');
check('party size 11 rejected',     V({name:'Juan Cruz', attending:'yes', partySize:'11'}).field, 'partySize');
check('party size 10 accepted',     V({name:'Juan Cruz', attending:'yes', partySize:'10'}).partySize, 10);

const yes = V({name:'  Juan   Dela  Cruz ',
               attending:'yes', partySize:'3', guestNames:'A\nB', message:'Congrats!'});
check('name whitespace collapsed',  yes.name, 'Juan Dela Cruz');
check('contact fields dropped',     [yes.email, yes.phone], [undefined, undefined]);
check('attending is boolean',       yes.attending, true);
check('party size parsed',          yes.partySize, 3);
check('message kept',               yes.message, 'Congrats!');

const no = V({name:'Maria Santos', attending:'no', partySize:'5', guestNames:'ignored', message:'Sorry!'});
check('decline forces 0 seats',     no.partySize, 0);
check('decline drops guest names',  no.guestNames, '');
check('decline keeps message',      no.message, 'Sorry!');

check('message truncated to 1000',  V({name:'Juan Cruz', attending:'no', message:'m'.repeat(1500)}).message.length, 1000);
check('guest names truncated',      V({name:'J C', attending:'yes', partySize:'2', guestNames:'g'.repeat(900)}).guestNames.length, 500);

// --- helpers ---------------------------------------------------------------
check('name normalised for matching', ctx.normalizeName_('  Juan  DELA cruz '), 'juandelacruz');
check('normalise handles null',       ctx.normalizeName_(null), '');
const code = ctx.makeCode_('Griffin Gamallo');
check('code shape', /^[A-Z]{3}-\d{4}$/.test(code), true);
check('code initials', code.slice(0, 3), 'GRI');
check('code falls back without letters', ctx.makeCode_('12345').slice(0, 3), 'RSV');

// --- deadline --------------------------------------------------------------
const realDate = Date;
const at = iso => { ctx.Date = class extends realDate { constructor(){ super(iso); } }; };
at('2026-08-13T00:00:00Z'); check('open well before deadline', ctx.isRsvpOpen_(), true);
at('2026-12-31T23:00:00Z'); check('open on the deadline day',  ctx.isRsvpOpen_(), true);
at('2027-01-01T00:00:00Z'); check('closed the day after',      ctx.isRsvpOpen_(), false);
ctx.Date = realDate;

// --- findExistingRow_ against a fake sheet ---------------------------------
const rows = [
  //  ts  upd  name             attending party names msg  code
  ['t','', 'Juan Dela Cruz', 'Yes', 2, '', '', 'JUA-1111'],
  ['t','', 'Maria Santos',   'No',  0, '', '', 'MAR-2222'],
];
const fakeSheet = {
  getLastRow: () => rows.length + 1,
  getRange: (r, c, nr, nc) => ({ getValues: () => rows.slice(r - 2, r - 2 + nr) })
};
const F = name => ctx.findExistingRow_(fakeSheet, { name });
check('matches on name',             F('Juan Dela Cruz'), 2);
check('name match ignores case/spacing', F('  maria   SANTOS '), 3);
check('unknown guest is new',        F('Louie Mendez'), 0);
check('empty sheet is new',          ctx.findExistingRow_({getLastRow: () => 1}, {name:'x'}), 0);

// --- honeypot and doPost ---------------------------------------------------
// Both run before any spreadsheet call, so no sheet stubs are needed here.
ctx.ContentService = {
  MimeType: { JSON: 'json' },
  createTextOutput(text) {
    return { text, mime: null, setMimeType(m) { this.mime = m; return this; } };
  }
};

const trap = ctx.handleRsvp_({ name: 'Spam Bot', attending: 'yes', partySize: '1',
                               website: 'http://buy-cheap-things.example' });
check('honeypot short-circuits',      trap.ok, true);
check('honeypot gives nothing away',  trap.code, 'THANK-YOU');

const post = body => JSON.parse(ctx.doPost({ postData: { contents: body } }).text);

// These two deliberately take the error path, which logs a stack. Hush it so
// a clean run stays readable.
const realError = ctx.console.error;
ctx.console.error = () => {};
check('doPost handles bad JSON',      post('not json{').ok, false);
check('doPost handles empty body',    post('{}').field, 'name');
check('doPost validates like the rest', post(JSON.stringify(
        { name: 'Juan Cruz' })).field, 'attending');
check('doPost honours the honeypot',  post(JSON.stringify(
        { name: 'Bot', attending: 'yes', website: 'x' })).ok, true);
check('doPost survives a missing event', JSON.parse(ctx.doPost().text).ok, false);
ctx.console.error = realError;

check('doPost replies as JSON',       ctx.doPost({ postData: { contents: '{}' } }).mime, 'json');

console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
