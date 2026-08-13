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

  // ---- RSVP deadline --------------------------------------------------------
  // rsvpDeadlineIso is the real cut-off. After the end of this day the form
  // closes itself and shows a polite "RSVPs have closed" message instead.
  rsvpDeadlineIso: '2026-12-31',
  rsvpDeadlineLabel: 'December 2026',

  // ---- Form behaviour -------------------------------------------------------
  maxPartySize: 10,          // largest number of seats one submission may claim
  askForPhone: true,         // set false to hide the phone number field
  allowEdits: true,          // re-submitting with the same name/email updates the
                             // existing row instead of creating a duplicate

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
    maxPartySize: CONFIG.maxPartySize,
    askForPhone: CONFIG.askForPhone,
    invitationLine: CONFIG.invitationLine,
    requestLine: CONFIG.requestLine,
    closingNote: CONFIG.closingNote,
    isOpen: isRsvpOpen_()
  };
}
