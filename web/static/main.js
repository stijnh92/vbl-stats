$(document).ready(function() {
  $('table').DataTable({
       paging: false,
        searching: false,
      info: false,
      order: [[ 2, "desc" ]]
  });
});
