function formateDateTime(datetime) {
  if (datetime == undefined || datetime == null) {
    return "NA"
  }
  const datetimeParts = datetime.split('T');
  const yearMonthDay = datetimeParts[0].split('-');
  return yearMonthDay[1] + '/' + yearMonthDay[2] + " " + datetimeParts[1]
}

function getBadgeType(status){
  var badgeLable = "badge-warning";
  switch (status) {
    case 'WAITING_4_WORKER':
      badgeLable = "badge-waiting"; break;
    case 'ERROR':
      badgeLable = "badge-error"; break;
    case 'HASH_MISMATCH':
      badgeLable = "badge-warning"; break;
    case 'COMPLETE':
      badgeLable = "badge-allok"; break;
    case 'STARTED':
      badgeLable = "badge-in-progress"; break;
    case 'LOADING_SNAPSHOT':
      badgeLable = "badge-in-progress"; break;
    case 'WORKING':
      badgeLable = "badge-in-progress"; break;
  }
  return badgeLable;
}
