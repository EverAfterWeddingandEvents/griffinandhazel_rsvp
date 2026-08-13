/**
 * Code.gs
 * -----------------------------------------------------------------------------
 * Web app entry point and the RSVP write path.
 *
 * Deploy:  Extensions > Apps Script > Deploy > New deployment > Web app
 *          Execute as: Me        Who has access: Anyone
 */

var HEADERS = [
  'Timestamp',
  'Last Updated',
  'Full Name',
  'Email',
  'Phone',
  'Attending',
  'Party Size',
  'Guest Names',
  'Message to the Couple',
  'Confirmation Code'
];

var COL = {
  timestamp: 1,
  updated: 2,
  name: 3,
  email: 4,
  phone: 5,
  attending: 6,
  partySize: 7,
  guestNames: 8,
  message: 9,
  code: 10
};


/* ========================================================================== */
/*  Web app                                                                   */
/* ========================================================================== */

function doGet() {
  var template = HtmlService.createTemplateFromFile('Index');
  template.configJson = JSON.stringify(getPublicConfig_());

  return template
    .evaluate()
    .setTitle(CONFIG.groom.split(' ')[0] + ' & ' + CONFIG.bride.split(' ')[0] + ' — RSVP')
    .addMetaTag('viewport', 'width=device-width, initial-scale=1')
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}


/**
 * Lets one HTML file pull in another (used for the CSS, JS and image files).
 */
function include(filename) {
  return HtmlService.createHtmlOutputFromFile(filename).getContent();
}


/* ========================================================================== */
/*  RSVP submission                                                           */
/* ========================================================================== */

/**
 * Called from the browser. Validates, then inserts or updates one row.
 *
 * @param {Object} payload  { name, email, phone, attending, partySize,
 *                            guestNames, message }
 * @return {Object}         { ok: true, code, name, attending, updated }
 *                          or { ok: false, error, field }
 */
function submitRsvp(payload) {
  try {
    if (!isRsvpOpen_()) {
      return fail_('RSVPs closed on ' + CONFIG.rsvpDeadlineLabel + '. Please contact the couple directly.');
    }

    var clean = validate_(payload || {});
    if (clean.error) {
      return clean;
    }

    var lock = LockService.getScriptLock();
    if (!lock.tryLock(20000)) {
      return fail_('The form is busy right now. Please try again in a moment.');
    }

    try {
      var sheet = getRsvpSheet_();
      var now = new Date();
      var existingRow = CONFIG.allowEdits ? findExistingRow_(sheet, clean) : 0;
      var isUpdate = existingRow > 0;

      var code = isUpdate
        ? (sheet.getRange(existingRow, COL.code).getDisplayValue() || makeCode_(clean.name))
        : makeCode_(clean.name);

      var row = [];
      row[COL.timestamp - 1] = now;
      row[COL.updated - 1] = isUpdate ? now : '';
      row[COL.name - 1] = clean.name;
      row[COL.email - 1] = clean.email;
      row[COL.phone - 1] = clean.phone;
      row[COL.attending - 1] = clean.attending ? 'Yes' : 'No';
      row[COL.partySize - 1] = clean.partySize;
      row[COL.guestNames - 1] = clean.guestNames;
      row[COL.message - 1] = clean.message;
      row[COL.code - 1] = code;

      if (isUpdate) {
        // Keep the original timestamp; only stamp "Last Updated".
        row[COL.timestamp - 1] = sheet.getRange(existingRow, COL.timestamp).getValue() || now;
        sheet.getRange(existingRow, 1, 1, HEADERS.length).setValues([row]);
      } else {
        sheet.appendRow(row);
      }

      SpreadsheetApp.flush();

      return {
        ok: true,
        code: code,
        name: clean.name,
        attending: clean.attending,
        partySize: clean.partySize,
        updated: isUpdate
      };

    } finally {
      lock.releaseLock();
    }

  } catch (err) {
    console.error(err && err.stack ? err.stack : err);
    return fail_('Something went wrong on our end. Please try again, or message the couple directly.');
  }
}


/* ========================================================================== */
/*  Validation                                                                */
/* ========================================================================== */

function validate_(p) {
  var name = trim_(p.name);
  if (name.length < 2) {
    return fail_('Please tell us your full name.', 'name');
  }
  if (name.length > 80) {
    return fail_('That name is a little too long for our sheet.', 'name');
  }

  var email = trim_(p.email).toLowerCase();
  if (email && !/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(email)) {
    return fail_('That email address does not look quite right.', 'email');
  }
  if (email.length > 120) {
    return fail_('That email address is too long.', 'email');
  }

  var phone = trim_(p.phone).slice(0, 40);

  if (p.attending !== 'yes' && p.attending !== 'no') {
    return fail_('Please let us know whether you can join us.', 'attending');
  }
  var attending = p.attending === 'yes';

  var partySize = 0;
  if (attending) {
    partySize = parseInt(p.partySize, 10);
    if (isNaN(partySize) || partySize < 1) {
      return fail_('Please tell us how many will be attending.', 'partySize');
    }
    if (partySize > CONFIG.maxPartySize) {
      return fail_('For parties larger than ' + CONFIG.maxPartySize +
        ', please contact the couple directly.', 'partySize');
    }
  }

  var guestNames = attending ? trim_(p.guestNames).slice(0, 500) : '';
  var message = trim_(p.message).slice(0, 1000);

  return {
    name: name,
    email: email,
    phone: phone,
    attending: attending,
    partySize: partySize,
    guestNames: guestNames,
    message: message
  };
}

function fail_(message, field) {
  return { ok: false, error: message, field: field || '' };
}

function trim_(v) {
  return String(v == null ? '' : v).replace(/\s+/g, ' ').trim();
}


/* ========================================================================== */
/*  Sheet helpers                                                             */
/* ========================================================================== */

function getRsvpSheet_() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName(CONFIG.sheetName);
  if (!sheet) {
    sheet = ss.insertSheet(CONFIG.sheetName);
  }
  if (sheet.getLastRow() === 0) {
    formatRsvpSheet_(sheet);
  }
  return sheet;
}


/**
 * Finds a previous RSVP from the same person so guests can change their answer.
 * Matches on email when one was given, otherwise on the normalised name.
 */
function findExistingRow_(sheet, clean) {
  var lastRow = sheet.getLastRow();
  if (lastRow < 2) {
    return 0;
  }

  var values = sheet.getRange(2, 1, lastRow - 1, HEADERS.length).getValues();
  var wantedEmail = clean.email;
  var wantedName = normalizeName_(clean.name);

  for (var i = values.length - 1; i >= 0; i--) {
    var rowEmail = String(values[i][COL.email - 1] || '').trim().toLowerCase();
    var rowName = normalizeName_(values[i][COL.name - 1]);

    if (wantedEmail) {
      if (rowEmail === wantedEmail) {
        return i + 2;
      }
    } else if (!rowEmail && rowName && rowName === wantedName) {
      return i + 2;
    }
  }
  return 0;
}

function normalizeName_(v) {
  return String(v == null ? '' : v).toLowerCase().replace(/[^a-z0-9]+/g, '');
}


/**
 * A short, human-readable confirmation code, e.g. "GAM-4821".
 */
function makeCode_(name) {
  var letters = String(name).toUpperCase().replace(/[^A-Z]/g, '').slice(0, 3) || 'RSV';
  var digits = String(Math.floor(1000 + Math.random() * 9000));
  return letters + '-' + digits;
}


/* ========================================================================== */
/*  Deadline                                                                  */
/* ========================================================================== */

/**
 * True until the end of the day named in CONFIG.rsvpDeadlineIso.
 */
function isRsvpOpen_() {
  var today = Utilities.formatDate(new Date(), CONFIG.timeZone, 'yyyy-MM-dd');
  return today <= CONFIG.rsvpDeadlineIso;
}
