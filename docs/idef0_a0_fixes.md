```html
<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<title>IDEF0 A1–A4 — Декомпозиция A0</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    background: #e8e8e8;
    font-family: Arial, sans-serif;
    display: flex;
    justify-content: center;
    align-items: flex-start;
    padding: 30px;
  }
  .sheet {
    width: 1200px;
    background: #fffff0;
    border: 2px solid #555;
    display: flex;
    flex-direction: column;
  }
</style>
</head>
<body>
<div class="sheet">

  <div style="display:grid; grid-template-columns: 220px 1fr; border-bottom: 2px solid #555;">
    <div style="border-right:1px solid #777; padding:5px 7px; font-size:10px; line-height:1.8;">
      <div><span style="color:#555;font-size:9px;">ИСПОЛЬЗУЕТСЯ В:</span></div>
      <div><span style="color:#555;font-size:9px;">АВТОР:</span> <b>Исаев Эльмар Хикметович</b></div>
      <div><span style="color:#555;font-size:9px;">ПРОЕКТ:</span> <b>AS-IS для магазина<br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;продажи продуктов</b></div>
      <div style="margin-top:3px;"><span style="color:#555;font-size:9px;">ЗАМЕЧАНИЯ:</span> 1 2 3 4 5 6 7 8 9 10</div>
    </div>
    <div style="display:grid; grid-template-columns: 130px 130px 1fr 100px; font-size:10px;">
      <div style="border-right:1px solid #777; padding:5px 7px; line-height:1.8;">
        <div><span style="color:#555;font-size:9px;">ДАТА:</span> <b>15.02.2026</b></div>
        <div><span style="color:#555;font-size:9px;">РЕВИЗИЯ:</span> <b>16.02.2026</b></div>
      </div>
      <div style="border-right:1px solid #777; padding:5px 7px; line-height:2.1; font-size:10px;">
        <div style="font-weight:bold; color:#c00;">РАЗРАБАТЫВАЕТСЯ</div>
        <div>ЧЕРНОВИК</div>
        <div>РЕКОМЕНДОВАНО</div>
        <div>ПУБЛИКАЦИЯ</div>
      </div>
      <div style="border-right:1px solid #777; padding:5px 7px; line-height:2.1;">
        <div style="color:#555;font-size:9px;">ЧИТАТЕЛЬ</div>
      </div>
      <div style="padding:5px 7px; text-align:center;">
        <div style="color:#555;font-size:9px;">КОНТЕКСТ:</div>
        <div style="font-weight:bold; font-size:11px; margin-top:10px;">A0</div>
      </div>
    </div>
  </div>

  <div style="height:820px;">
  <svg width="1200" height="820" viewBox="0 0 1200 820">
    <defs>
      <marker id="arr" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto">
        <polygon points="0 0,10 4,0 8" fill="#222"/>
      </marker>
      <marker id="arr-pink" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto">
        <polygon points="0 0,10 4,0 8" fill="#cc44aa"/>
      </marker>
      <marker id="arr-navy" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto">
        <polygon points="0 0,10 4,0 8" fill="#2244cc"/>
      </marker>
      <marker id="arr-orange" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto">
        <polygon points="0 0,10 4,0 8" fill="#cc4400"/>
      </marker>
      <marker id="arr-purple" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto">
        <polygon points="0 0,10 4,0 8" fill="#8800cc"/>
      </marker>
      <marker id="arr-red" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto">
        <polygon points="0 0,10 4,0 8" fill="#cc0000"/>
      </marker>
      <marker id="arr-green" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto">
        <polygon points="0 0,10 4,0 8" fill="#008800"/>
      </marker>
    </defs>

    <rect x="40" y="310" width="190" height="120" fill="white" stroke="#333" stroke-width="1.8"/>
    <text x="135" y="363" font-family="Arial" font-size="12" font-weight="bold" fill="#111" text-anchor="middle">Приём</text>
    <text x="135" y="379" font-family="Arial" font-size="12" font-weight="bold" fill="#111" text-anchor="middle">заказа</text>
    <text x="224" y="424" font-family="Arial" font-size="10" fill="#555" text-anchor="end">A1</text>

    <rect x="310" y="310" width="190" height="120" fill="white" stroke="#333" stroke-width="1.8"/>
    <text x="405" y="363" font-family="Arial" font-size="12" font-weight="bold" fill="#111" text-anchor="middle">Сборка</text>
    <text x="405" y="379" font-family="Arial" font-size="12" font-weight="bold" fill="#111" text-anchor="middle">заказа</text>
    <text x="494" y="424" font-family="Arial" font-size="10" fill="#555" text-anchor="end">A2</text>

    <rect x="580" y="310" width="190" height="120" fill="white" stroke="#333" stroke-width="1.8"/>
    <text x="675" y="363" font-family="Arial" font-size="12" font-weight="bold" fill="#111" text-anchor="middle">Оплата</text>
    <text x="675" y="379" font-family="Arial" font-size="12" font-weight="bold" fill="#111" text-anchor="middle">заказа</text>
    <text x="764" y="424" font-family="Arial" font-size="10" fill="#555" text-anchor="end">A3</text>

    <rect x="850" y="310" width="190" height="120" fill="white" stroke="#333" stroke-width="1.8"/>
    <text x="945" y="363" font-family="Arial" font-size="12" font-weight="bold" fill="#111" text-anchor="middle">Доставка</text>
    <text x="945" y="379" font-family="Arial" font-size="12" font-weight="bold" fill="#111" text-anchor="middle">заказа</text>
    <text x="1034" y="424" font-family="Arial" font-size="10" fill="#555" text-anchor="end">A4</text>

    <line x1="5" y1="350" x2="40" y2="350" stroke="#222" stroke-width="1.4" marker-end="url(#arr)"/>
    <text x="8" y="342" font-family="Arial" font-size="10" fill="#111">Запрос клиента</text>
    <text x="8" y="355" font-family="Arial" font-size="8.5" fill="#666">(звонок / визит)</text>

    <line x1="230" y1="360" x2="310" y2="360" stroke="#222" stroke-width="1.4" marker-end="url(#arr)"/>
    <text x="234" y="352" font-family="Arial" font-size="9" fill="#333">Принятый заказ</text>
    <text x="234" y="363" font-family="Arial" font-size="8" fill="#666">(список товаров)</text>

    <polyline points="135,310 135,270 675,270 675,310" fill="none" stroke="#222" stroke-width="1.3" marker-end="url(#arr)"/>
    <text x="370" y="262" font-family="Arial" font-size="9" fill="#333" text-anchor="middle">Сумма к оплате</text>

    <line x1="500" y1="365" x2="850" y2="365" stroke="#222" stroke-width="1.4" marker-end="url(#arr)"/>
    <text x="672" y="357" font-family="Arial" font-size="9" fill="#333" text-anchor="middle">Собранный заказ</text>
    <text x="672" y="368" font-family="Arial" font-size="8" fill="#666" text-anchor="middle">(список товаров)</text>

    <line x1="770" y1="360" x2="850" y2="360" stroke="#222" stroke-width="1.4" marker-end="url(#arr)"/>
    <text x="774" y="352" font-family="Arial" font-size="9" fill="#333">Подтв. оплаты</text>

    <line x1="770" y1="395" x2="850" y2="395" stroke="#222" stroke-width="1.3" stroke-dasharray="5 3" marker-end="url(#arr)"/>
    <text x="774" y="388" font-family="Arial" font-size="8.5" fill="#666">Оплата при получении</text>

    <line x1="5" y1="415" x2="580" y2="415" stroke="#222" stroke-width="1.4" marker-end="url(#arr)"/>
    <text x="8" y="407" font-family="Arial" font-size="10" fill="#111">Оплата (предоплата)</text>
    <text x="8" y="419" font-family="Arial" font-size="8.5" fill="#666">(наличные / карта)</text>

    <line x1="770" y1="420" x2="1195" y2="420" stroke="#222" stroke-width="1.4" marker-end="url(#arr)"/>
    <text x="800" y="412" font-family="Arial" font-size="10" fill="#111">Выданный чек</text>
    <text x="800" y="424" font-family="Arial" font-size="8.5" fill="#666">(бумажный)</text>

    <line x1="1040" y1="380" x2="1195" y2="380" stroke="#222" stroke-width="1.4" marker-end="url(#arr)"/>
    <text x="1044" y="372" font-family="Arial" font-size="10" fill="#111">Товар</text>
    <text x="1044" y="384" font-family="Arial" font-size="8.5" fill="#666">(доставленный заказ)</text>

    <line x1="80" y1="60" x2="1100" y2="60" stroke="#aaa" stroke-width="1" stroke-dasharray="5 3"/>

    <line x1="100" y1="60" x2="100" y2="310" stroke="#cc44aa" stroke-width="1.3" marker-end="url(#arr-pink)"/>
    <text x="103" y="90" font-family="Arial" font-size="8.5" fill="#cc44aa">Закон «О защите</text>
    <text x="103" y="101" font-family="Arial" font-size="8.5" fill="#cc44aa">прав потребителей»</text>

    <line x1="650" y1="60" x2="650" y2="310" stroke="#222" stroke-width="1.3" marker-end="url(#arr)"/>
    <text x="653" y="90" font-family="Arial" font-size="8.5" fill="#222">Налоговый</text>
    <text x="653" y="101" font-family="Arial" font-size="8.5" fill="#222">кодекс РФ</text>

    <line x1="380" y1="60" x2="380" y2="310" stroke="#2244cc" stroke-width="1.3" marker-end="url(#arr-navy)"/>
    <text x="383" y="90" font-family="Arial" font-size="8.5" fill="#2244cc">Правила</text>
    <text x="383" y="101" font-family="Arial" font-size="8.5" fill="#2244cc">торговли</text>

    <line x1="940" y1="60" x2="940" y2="310" stroke="#cc4400" stroke-width="1.3" marker-end="url(#arr-orange)"/>
    <text x="943" y="90" font-family="Arial" font-size="8.5" fill="#cc4400">Гражданский</text>
    <text x="943" y="101" font-family="Arial" font-size="8.5" fill="#cc4400">кодекс РФ</text>

    <line x1="80" y1="760" x2="1100" y2="760" stroke="#aaa" stroke-width="1" stroke-dasharray="5 3"/>

    <line x1="100" y1="760" x2="100" y2="430" stroke="#8800cc" stroke-width="1.3" marker-end="url(#arr-purple)"/>
    <text x="103" y="750" font-family="Arial" font-size="9" fill="#8800cc">Менеджер</text>

    <line x1="660" y1="760" x2="660" y2="430" stroke="#8800cc" stroke-width="1.3" stroke-dasharray="5 3" marker-end="url(#arr-purple)"/>
    <text x="663" y="750" font-family="Arial" font-size="9" fill="#8800cc">Менеджер</text>

    <line x1="390" y1="760" x2="390" y2="430" stroke="#cc0000" stroke-width="1.3" marker-end="url(#arr-red)"/>
    <text x="393" y="750" font-family="Arial" font-size="9" fill="#cc0000">Сборщик</text>

    <line x1="950" y1="760" x2="950" y2="430" stroke="#008800" stroke-width="1.3" marker-end="url(#arr-green)"/>
    <text x="953" y="750" font-family="Arial" font-size="9" fill="#008800">Курьер</text>

    <line x1="165" y1="760" x2="165" y2="430" stroke="#222" stroke-width="1.3" marker-end="url(#arr)"/>
    <text x="168" y="750" font-family="Arial" font-size="9" fill="#222">Бумага / тетрадь</text>

    <line x1="430" y1="760" x2="430" y2="430" stroke="#222" stroke-width="1.3" stroke-dasharray="5 3" marker-end="url(#arr)"/>
    <text x="433" y="750" font-family="Arial" font-size="9" fill="#222">Бумага (список)</text>

  </svg>
  </div>

  <div style="display:grid; grid-template-columns: 160px 1fr 150px; border-top: 2px solid #555; font-size:10px;">
    <div style="border-right:1px solid #777; padding:6px 8px;">
      <span style="color:#666;font-size:9px;">Ветка:</span> <b>A0</b>
    </div>
    <div style="border-right:1px solid #777; padding:6px 8px; text-align:center;">
      <span style="color:#666;font-size:9px;">Название:</span><br>
      <b style="font-size:14px;">Продажа продуктов</b>
    </div>
    <div style="padding:6px 8px; text-align:center;">
      <span style="color:#666;font-size:9px;">Номер:</span><br>
      <b style="font-size:13px;">2</b>
    </div>
  </div>

</div>
</body>
</html>
```
