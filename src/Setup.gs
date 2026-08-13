/**
 * Setup.gs
 * -----------------------------------------------------------------------------
 * One-time spreadsheet setup, formatting, and the live summary tab.
 *
 * After pasting the project in, run "Wedding RSVP > Set up spreadsheet" from the
 * spreadsheet menu once. Everything after that is automatic.
 */

var PALETTE = {
  header: '#8C6A55',
  headerText: '#FFFFFF',
  band: '#FBF7F1',
  yes: '#E8F0E4',
  no: '#F7E9E4',
  rule: '#E4D8C8'
};


/**
 * Adds the custom menu to the spreadsheet.
 */
function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('💍 Wedding RSVP')
    .addItem('Set up spreadsheet', 'setupSpreadsheet')
    .addItem('Refresh summary', 'refreshSummary')
    .addSeparator()
    .addItem('Show RSVP form link', 'showFormUrl')
    .addToUi();
}


/**
 * Creates and formats the RSVP sheet and the Summary sheet.
 * Safe to run more than once — it will not delete existing responses.
 */
function setupSpreadsheet() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  ss.setSpreadsheetTimeZone(CONFIG.timeZone);

  var sheet = ss.getSheetByName(CONFIG.sheetName) || ss.insertSheet(CONFIG.sheetName);
  formatRsvpSheet_(sheet);
  buildSummarySheet_(ss);

  ss.setActiveSheet(sheet);

  SpreadsheetApp.getUi().alert(
    'All set!',
    'The "' + CONFIG.sheetName + '" and "' + CONFIG.summarySheetName + '" tabs are ready.\n\n' +
    'Next: Deploy > New deployment > Web app, set "Who has access" to Anyone, ' +
    'and share that link with your guests.',
    SpreadsheetApp.getUi().ButtonSet.OK
  );
}


function formatRsvpSheet_(sheet) {
  // Header row
  var header = sheet.getRange(1, 1, 1, HEADERS.length);
  header.setValues([HEADERS]);
  header.setFontWeight('bold')
    .setFontFamily('Georgia')
    .setFontSize(11)
    .setBackground(PALETTE.header)
    .setFontColor(PALETTE.headerText)
    .setVerticalAlignment('middle');

  sheet.setRowHeight(1, 34);
  sheet.setFrozenRows(1);

  // Column widths
  var widths = [150, 150, 210, 230, 140, 100, 95, 260, 380, 130];
  for (var i = 0; i < widths.length; i++) {
    sheet.setColumnWidth(i + 1, widths[i]);
  }

  // Number / text formats
  sheet.getRange(2, COL.timestamp, sheet.getMaxRows() - 1, 1)
    .setNumberFormat('mmm d, yyyy  h:mm am/pm');
  sheet.getRange(2, COL.updated, sheet.getMaxRows() - 1, 1)
    .setNumberFormat('mmm d, yyyy  h:mm am/pm');
  sheet.getRange(2, COL.partySize, sheet.getMaxRows() - 1, 1)
    .setHorizontalAlignment('center');
  sheet.getRange(2, COL.attending, sheet.getMaxRows() - 1, 1)
    .setHorizontalAlignment('center');
  sheet.getRange(2, COL.guestNames, sheet.getMaxRows() - 1, 2)
    .setWrap(true)
    .setVerticalAlignment('top');

  // Colour-code the Attending column
  var attendingRange = sheet.getRange(2, COL.attending, sheet.getMaxRows() - 1, 1);
  var rules = [
    SpreadsheetApp.newConditionalFormatRule()
      .whenTextEqualTo('Yes')
      .setBackground(PALETTE.yes)
      .setFontColor('#3F6136')
      .setBold(true)
      .setRanges([attendingRange])
      .build(),
    SpreadsheetApp.newConditionalFormatRule()
      .whenTextEqualTo('No')
      .setBackground(PALETTE.no)
      .setFontColor('#8C4A38')
      .setRanges([attendingRange])
      .build()
  ];
  sheet.setConditionalFormatRules(rules);

  sheet.getRange(1, 1, sheet.getMaxRows(), HEADERS.length)
    .setBorder(null, null, null, null, null, true, PALETTE.rule, SpreadsheetApp.BorderStyle.SOLID);

  // Trim unused columns so the sheet looks tidy
  var extra = sheet.getMaxColumns() - HEADERS.length;
  if (extra > 0) {
    sheet.deleteColumns(HEADERS.length + 1, extra);
  }
}


function buildSummarySheet_(ss) {
  var name = CONFIG.summarySheetName;
  var sheet = ss.getSheetByName(name) || ss.insertSheet(name, 0);
  sheet.clear();
  sheet.clearConditionalFormatRules();

  var data = CONFIG.sheetName;
  var q = "'" + data + "'";

  sheet.getRange('B2').setValue(CONFIG.groom + '  &  ' + CONFIG.bride)
    .setFontFamily('Georgia').setFontSize(18).setFontColor('#5A4636');
  sheet.getRange('B3').setValue(CONFIG.weddingDateShort + '  ·  ' + CONFIG.ceremony.city)
    .setFontFamily('Georgia').setFontSize(11).setFontColor('#8B7A69');

  var rows = [
    ['Responses received', '=COUNTA(' + q + '!C2:C)'],
    ['Joyfully accepting', '=COUNTIF(' + q + '!F2:F,"Yes")'],
    ['Regretfully declining', '=COUNTIF(' + q + '!F2:F,"No")'],
    ['Total seats confirmed', '=SUM(' + q + '!G2:G)'],
    ['Messages left for the couple', '=COUNTA(' + q + '!I2:I)'],
    ['RSVP deadline', CONFIG.rsvpDeadlineLabel],
    ['Days until the wedding', '=MAX(0, DATE(' +
      CONFIG.weddingDateIso.split('-').join(',') + ') - TODAY())']
  ];

  sheet.getRange(5, 2, rows.length, 2).setValues(rows);
  sheet.getRange(5, 2, rows.length, 1)
    .setFontFamily('Georgia').setFontSize(11).setFontColor('#5A4636');
  sheet.getRange(5, 3, rows.length, 1)
    .setFontFamily('Georgia').setFontSize(16).setFontWeight('bold')
    .setFontColor('#8C6A55').setHorizontalAlignment('right');

  sheet.setColumnWidth(1, 40);
  sheet.setColumnWidth(2, 300);
  sheet.setColumnWidth(3, 140);
  sheet.setHiddenGridlines(true);
  sheet.getRange('A1:E20').setBackground(PALETTE.band);
}


function refreshSummary() {
  buildSummarySheet_(SpreadsheetApp.getActiveSpreadsheet());
  SpreadsheetApp.getActiveSpreadsheet().toast('Summary refreshed.', '💍 Wedding RSVP', 3);
}


/**
 * Shows the deployed web app URL so it is easy to copy and share.
 */
function showFormUrl() {
  var url = ScriptApp.getService().getUrl();
  var ui = SpreadsheetApp.getUi();
  if (!url) {
    ui.alert('Not deployed yet',
      'Deploy the web app first: Extensions > Apps Script > Deploy > New deployment > Web app.',
      ui.ButtonSet.OK);
    return;
  }
  ui.alert('Your RSVP link', url, ui.ButtonSet.OK);
}
