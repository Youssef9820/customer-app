// ====== global.js ======
// Shared JS for all pages (Select2, Notifications, Spinner)

$(document).ready(function () {

    // 🔹 Universal Select2 Setup
    $('select').select2({
        placeholder: "Select an option",
        allowClear: true,
        theme: "bootstrap4",
        width: '100%'
    });

    // 🔹 Spinner Helper
    window.addSpinner = function ($btn, text = "Loading...") {
        $btn.html('<i class="tim-icons icon-refresh-01 spinning"></i> ' + text);
        $btn.prop('disabled', true);
    };

    // 🔹 Spinner Animation Style
    if (!document.getElementById('spinner-style')) {
        var style = document.createElement('style');
        style.id = 'spinner-style';
        style.innerHTML = `
            @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
            .spinning { animation: spin 1s linear infinite; display: inline-block; }
        `;
        document.head.appendChild(style);
    }

    // 🔹 Notification System
    window.showNotification = function (message, type = 'success') {
        var color = type === 'warning' ? '#fb6340' :
                    type === 'danger' ? '#f5365c' : '#2dce89';
        var notification = $('<div>').css({
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
        }).html('<i class="tim-icons icon-bell-55"></i> ' + message)
          .appendTo('body');

        setTimeout(() => notification.css({ opacity: 1, transform: 'translateY(0)' }), 100);
        setTimeout(() => {
            notification.css({ opacity: 0, transform: 'translateY(-20px)' });
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    };
});
