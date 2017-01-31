var diff_match_patch=require('googlediff');
var dmp =new diff_match_patch();

function launch() {
  var text1 = "this is some test. blah blah blah";
  var text2 = "this is other text. blah blah blah";
  //dmp.Diff_Timeout = 1; // set 0 for no timeout

  var ms_start = (new Date()).getTime();
  var d = dmp.diff_main(text1, text2);
  var ms_end = (new Date()).getTime();

  if (true) {
    dmp.diff_cleanupSemantic(d);
  }
  if (false) {
    dmp.Diff_EditCost = 4;
    dmp.diff_cleanupEfficiency(d);
  }
  //var ds = dmp.diff_prettyHtml(d);
  //console.log(ds + '<br/>Time: ' + (ms_end - ms_start) / 1000 + 's');
  console.log(d)
}
launch();
