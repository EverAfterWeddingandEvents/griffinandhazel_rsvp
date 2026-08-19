/**
 * Config.gs
 * -----------------------------------------------------------------------------
 * Every detail you are likely to want to change lives in this one file.
 * Edit the values below, save, and re-deploy the web app.
 */

var CONFIG = {

  // ---- The couple -----------------------------------------------------------
  groom: 'Griffin Paul M. Gamallo',
  bride: 'Hazel Jade A. Gamallo',
  monogram: 'G & H',

  // ---- The day --------------------------------------------------------------
  // weddingDateIso drives the countdown. Keep it in YYYY-MM-DD form.
  weddingDateIso: '2027-05-08',
  weddingDateLong: 'Saturday, the Eighth of May',
  weddingYear: 'Two Thousand Twenty-Seven',
  weddingDateShort: 'May 8, 2027',

  // ---- Ceremony & reception -------------------------------------------------
  // Leave a time as '' (empty) and it simply will not be displayed.
  ceremony: {
    title: 'The Ceremony',
    venue: 'Our Lady of the Most Holy Rosary Cathedral Parish',
    city: 'Dipolog City',
    time: ''
  },
  reception: {
    title: 'The Reception',
    venue: 'Ariana Hotel',
    city: 'Dipolog City',
    time: 'Reception to follow'
  },

  // ---- Where to stay --------------------------------------------------------
  // A few rooms are held at the reception venue. The site does not take
  // bookings itself — it points guests at the front desk, who do. Set enabled
  // to false and the card disappears from the page entirely.
  accommodation: {
    enabled: true,
    title: 'Staying the Night',
    // One line, no + concatenation: build_site.py reads this file as a literal.
    note: 'A few rooms are available at Ariana Hotel. To reserve one, please contact the front desk directly.',
    phones: ['0998-951-7476', '0917-535-9011'],
    email: 'arianahotel.frontdesk@gmail.com'
  },

  // ---- RSVP deadline --------------------------------------------------------
  // rsvpDeadlineIso is the real cut-off. After the end of this day the form
  // closes itself and shows a polite "RSVPs have closed" message instead.
  rsvpDeadlineIso: '2026-12-31',
  rsvpDeadlineLabel: 'December 2026',

  // ---- Form behaviour -------------------------------------------------------
  maxPartySize: 2,           // largest number of seats one submission may claim.
                             // At 2 the form drops the "how many" counter and
                             // simply asks for the one companion's name.
  allowEdits: true,          // re-submitting under the same name updates that
                             // guest's row instead of adding a duplicate

  // ---- Atmosphere -----------------------------------------------------------
  // All three are ignored for guests whose device asks for reduced motion.
  animations: true,          // GSAP entrance timeline and scroll reveals
  petals: true,              // petals drifting down the background
  petalCount: 14,

  music: {
    enabled: true,
    label: 'Play our song',  // the little tooltip beside the button
    volume: 0.32,            // 0 to 1
    // Browsers refuse to play audio until the guest interacts with the page,
    // so nothing can start on load. true starts it on their first tap or key
    // press anywhere; false waits until they press the music button itself.
    startOnFirstTap: true
  },

  // ---- Spreadsheet ----------------------------------------------------------
  sheetName: 'RSVPs',
  summarySheetName: 'Summary',

  // ---- Wording --------------------------------------------------------------
  invitationLine: 'Together with their families',
  requestLine: 'request the honour of your presence',
  closingNote: 'We cannot wait to celebrate with you.',

  // ---- Time zone used for the deadline check --------------------------------
  timeZone: 'Asia/Manila'
};


/**
 * The subset of CONFIG that is safe (and useful) to hand to the browser.
 */
function getPublicConfig_() {
  return {
    groom: CONFIG.groom,
    bride: CONFIG.bride,
    monogram: CONFIG.monogram,
    weddingDateIso: CONFIG.weddingDateIso,
    weddingDateLong: CONFIG.weddingDateLong,
    weddingYear: CONFIG.weddingYear,
    weddingDateShort: CONFIG.weddingDateShort,
    ceremony: CONFIG.ceremony,
    reception: CONFIG.reception,
    rsvpDeadlineIso: CONFIG.rsvpDeadlineIso,
    rsvpDeadlineLabel: CONFIG.rsvpDeadlineLabel,
    accommodation: CONFIG.accommodation,
    maxPartySize: CONFIG.maxPartySize,
    animations: CONFIG.animations,
    petals: CONFIG.petals,
    petalCount: CONFIG.petalCount,
    music: CONFIG.music,
    invitationLine: CONFIG.invitationLine,
    requestLine: CONFIG.requestLine,
    closingNote: CONFIG.closingNote,
    isOpen: isRsvpOpen_()
  };
}
