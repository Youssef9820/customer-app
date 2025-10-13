$(document).ready(function() {
    $('#instructor-select').select2({
        placeholder: "🔍 Search by name or email...",
        allowClear: true,
        theme: "bootstrap4",
        width: '100%'
    });

    $('#year_filter').select2({ placeholder: "Select a Year", allowClear: true, theme: "bootstrap4", width: '100%' });
    $('#university_filter').select2({ placeholder: "Search for a University", allowClear: true, theme: "bootstrap4", width: '100%' });
    $('#college_filter').select2({ placeholder: "Search for a College", allowClear: true, theme: "bootstrap4", width: '100%' });

    $('#instructor-report-form').on('submit', function(e) {
        e.preventDefault();
        var instructorId = $('#instructor-select').val();
        if (instructorId) {
            var $btn = $(this).find('button[type="submit"]');
            $btn.html('<i class="tim-icons icon-refresh-01 spinning"></i> Generating...');
            $btn.prop('disabled', true);
            var reportUrl = window.reportsUrls.instructorReport.replace("0", instructorId);
            setTimeout(function() { window.location.href = reportUrl; }, 500);
        } else {
            showNotification('Please select an instructor to generate a report', 'warning');
        }
    });

    var style = document.createElement('style');
    style.innerHTML = `
        @keyframes spin { 
            from { transform: rotate(0deg); } 
            to { transform: rotate(360deg); } 
        } 
        .spinning { 
            animation: spin 1s linear infinite; 
            display: inline-block; 
        }`;
    document.head.appendChild(style);

    function showNotification(message, type) {
        var color = type === 'warning' ? '#fb6340' : '#2dce89';
        var notification = $('<div>')
            .css({
                position: 'fixed',
                top: '20px',
                right: '20px',
                background: 'linear-gradient(135deg, ' + color + ' 0%, ' + color + 'dd 100%)',
                color: '#fff',
                padding: '16px 24px',
                borderRadius: '12px',
                boxShadow: '0 8px 24px rgba(0,0,0,0.3)',
                zIndex: 9999,
                fontSize: '15px',
                fontWeight: '500',
                opacity: 0,
                transform: 'translateY(-20px)',
                transition: 'all 0.3s ease'
            })
            .html('<i class="tim-icons icon-bell-55"></i> ' + message)
            .appendTo('body');

        setTimeout(function() { 
            notification.css({ opacity: 1, transform: 'translateY(0)' }); 
        }, 100);

        setTimeout(function() { 
            notification.css({ opacity: 0, transform: 'translateY(-20px)' }); 
            setTimeout(function() { notification.remove(); }, 300); 
        }, 3000);
    }
});
