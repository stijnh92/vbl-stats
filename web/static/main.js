$(document).ready(function () {
    function initDataTable() {

        var table = $('.team-table');
        var length = table.find("tr:first th").length;
        var defaultSort = length === 10 ? 3 : 2;

        var t = table.DataTable({
            paging: false,
            searching: false,
            info: false,
            order: [[defaultSort, "desc"]]
        });

        t.on('order.dt', function () {
            t.column(0, {order: 'applied'}).nodes().each(function (cell, i) {
                cell.innerHTML = i + 1;
            });
        }).draw();
    }

    initDataTable();

    $('body')
        .on('click', '#btn_show_totals', function() {
            updateTable('totals');
    })
        .on('click', '#btn_show_average', function() {
            updateTable('average');
    });

    function updateTable(format) {
        var endpoint = window.location.pathname;
        $.get(endpoint + '?tableOnly=1&format=' + format, function (data) {
            $('#overview').replaceWith(data);
            initDataTable();
        });
    }
});
