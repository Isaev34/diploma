(function() {
    // Ждем полной загрузки DOM
    window.addEventListener('load', function() {
        const barcodeField = document.querySelector('#id_barcode');
        if (!barcodeField) return;
        if (window.location.protocol !== 'https:' && window.location.hostname !== 'localhost') {
            btn.innerText = '⚠️ Нужен HTTPS для камеры';
            btn.disabled = true;
            btn.style.background = 'gray';
        }
        // Создаем кнопку
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.innerText = '📷 ЗАПУСТИТЬ КАМЕРУ';
        btn.style = 'display:block; margin: 10px 0; padding: 10px; background: #417690; color: white; border: none; border-radius: 4px; cursor: pointer;';
        
        // Создаем контейнер для сканера
        const scannerContainer = document.createElement('div');
        scannerContainer.id = 'interactive-scanner';
        scannerContainer.style = 'width: 100%; max-width: 500px; margin-top: 10px;';

        barcodeField.parentNode.appendChild(btn);
        barcodeField.parentNode.appendChild(scannerContainer);

        let html5QrCode;

        btn.onclick = function() {
            if (!html5QrCode) {
                html5QrCode = new Html5Qrcode("interactive-scanner");
            }

            const config = { fps: 10, qrbox: { width: 250, height: 150 } };

            html5QrCode.start(
                { facingMode: "environment" }, 
                config,
                (decodedText) => {
                    barcodeField.value = decodedText;
                    html5QrCode.stop();
                    alert("Считано: " + decodedText);
                },
                (errorMessage) => {
                    // Это вызывается постоянно при поиске кода, тут лучше ничего не писать
                }
            ).catch(err => {
                console.error("Ошибка запуска:", err);
                alert("Камера не запустилась. Причина: " + err);
            });
        };
    });
})();