(function () {
  'use strict';

  // Rechtsstand 04.10.2026. Zulagen: Altersvorsorgereformgesetz (BGBl. 2026 I Nr. 156).
  // Tarif: § 32a EStG 2026; der Tarif 2027 liegt nur als Regierungsentwurf vor.
  var MIN_EIGENBEITRAG = 120;
  var GRENZE_STUFE_1 = 360;
  var GEFOERDERT_MAX = 1800;
  var KIND_MAX = 300;
  var ABGELTUNGSTEUER = 0.25;
  var TEILFREISTELLUNG = 0.30;
  var INFLATION = 0.02;
  var SZENARIEN = [0.02, 0.04, 0.06];

  function estGrundtarif(zve) {
    var x = Math.floor(zve);
    var st;
    if (x <= 12348) {
      st = 0;
    } else if (x <= 17799) {
      var y = (x - 12348) / 10000;
      st = (914.51 * y + 1400) * y;
    } else if (x <= 69878) {
      var z = (x - 17799) / 10000;
      st = (173.10 * z + 2397) * z + 1034.87;
    } else if (x <= 277825) {
      st = 0.42 * x - 11135.63;
    } else {
      st = 0.45 * x - 19470.38;
    }
    return Math.floor(st);
  }

  function est(zve, splitting) {
    return splitting ? 2 * estGrundtarif(Math.floor(zve / 2)) : estGrundtarif(zve);
  }

  function foerderung(e, kinder, zve, splitting) {
    var grund = 0;
    var kind = 0;
    if (e >= MIN_EIGENBEITRAG) {
      grund = 0.5 * Math.min(e, GRENZE_STUFE_1) +
        0.25 * Math.max(Math.min(e, GEFOERDERT_MAX) - GRENZE_STUFE_1, 0);
      kind = kinder * Math.min(e, KIND_MAX);
    }
    var zulagen = grund + kind;
    var abzug = Math.min(e, GEFOERDERT_MAX) + zulagen;
    var entlastung = est(zve, splitting) - est(Math.max(zve - abzug, 0), splitting);
    var zusatz = Math.max(0, entlastung - zulagen);
    var zufluss = e + zulagen;
    return {
      grund: grund, kind: kind, zulagen: zulagen, abzug: abzug,
      entlastung: entlastung, zusatz: zusatz, gesamt: zulagen + zusatz,
      zufluss: zufluss, netto: e - zusatz,
      quote: zufluss > 0 ? (zulagen + zusatz) / zufluss : 0
    };
  }

  function rentenfaktor(r, n) {
    return r === 0 ? n : (Math.pow(1 + r, n) - 1) / r;
  }

  function projektion(f, jahre, steuerAlter) {
    return SZENARIEN.map(function (r) {
      var kapital = f.zufluss * rentenfaktor(r, jahre);
      var steuer = kapital * steuerAlter;
      var avNetto = kapital - steuer;
      var frei = f.netto * rentenfaktor(r, jahre);
      var gewinn = Math.max(frei - f.netto * jahre, 0);
      var freiNetto = frei - gewinn * (1 - TEILFREISTELLUNG) * ABGELTUNGSTEUER;
      return {
        r: r, kapital: kapital, steuer: steuer, avNetto: avNetto,
        freiNetto: freiNetto, diff: avNetto - freiNetto,
        real: kapital / Math.pow(1 + INFLATION, jahre)
      };
    });
  }

  var fmtGanz = new Intl.NumberFormat('de-DE', { maximumFractionDigits: 0 });
  var fmtCent = new Intl.NumberFormat('de-DE', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

  function eur(v) {
    var gerundet = Math.round(v * 100) / 100;
    var text = Number.isInteger(gerundet) ? fmtGanz.format(gerundet) : fmtCent.format(gerundet);
    return text + ' EUR';
  }

  function eurRund(v) {
    return fmtGanz.format(Math.round(v)) + ' EUR';
  }

  function zahl(v) {
    return fmtGanz.format(Math.round(v));
  }

  function zahlDiff(v) {
    var r = Math.round(v);
    return (r > 0 ? '+' : r < 0 ? '\u2212' : '') + fmtGanz.format(Math.abs(r));
  }

  function prozent(v) {
    return fmtGanz.format(Math.round(v * 100)) + ' %';
  }

  var FELDER = {
    beitrag: { min: 0, max: 1800, text: 'Bitte einen Betrag zwischen 0 und 1.800 EUR eingeben.' },
    kinder: { min: 0, max: 9, text: 'Bitte eine ganze Zahl zwischen 0 und 9 eingeben.' },
    zve: { min: 0, max: 5000000, text: 'Bitte einen Betrag zwischen 0 und 5.000.000 EUR eingeben.' },
    jahre: { min: 1, max: 50, text: 'Bitte eine ganze Zahl zwischen 1 und 50 eingeben.' },
    steueralter: { min: 0, max: 45, text: 'Bitte einen Wert zwischen 0 und 45 % eingeben.' }
  };

  function init(root) {
    function feld(name) { return root.querySelector('[data-feld="' + name + '"]'); }
    function out(name, text) {
      var el = root.querySelector('[data-out="' + name + '"]');
      if (el) { el.textContent = text; }
    }

    function lesen() {
      var werte = {};
      var ok = true;
      Object.keys(FELDER).forEach(function (name) {
        var input = feld(name);
        var regel = FELDER[name];
        var roh = input.value.trim().replace(',', '.');
        var wert = Number(roh);
        var ganz = name === 'kinder' || name === 'jahre';
        var gueltig = roh !== '' && isFinite(wert) && wert >= regel.min && wert <= regel.max &&
          (!ganz || Number.isInteger(wert));
        var fehler = root.querySelector('#' + input.id + '-fehler');
        if (gueltig) {
          input.removeAttribute('aria-invalid');
          fehler.hidden = true;
          fehler.textContent = '';
          werte[name] = wert;
        } else {
          input.setAttribute('aria-invalid', 'true');
          fehler.textContent = regel.text;
          fehler.hidden = false;
          ok = false;
        }
      });
      var split = root.querySelector('[data-feld="splitting"]:checked');
      werte.splitting = !!split && split.value === '1';
      return ok ? werte : null;
    }

    function rechnen() {
      var w = lesen();
      root.classList.toggle('bk-avd-ungueltig', !w);
      if (!w) {
        out('kern', 'Bitte prüfen Sie die markierten Eingaben.');
        out('fazit', '');
        return;
      }
      var f = foerderung(w.beitrag, w.kinder, w.zve, w.splitting);
      var p = projektion(f, w.jahre, w.steueralter / 100);

      out('grund', eur(f.grund));
      out('kind', eur(f.kind));
      out('entlastung', eur(f.entlastung));
      out('zusatz', eur(f.zusatz));
      out('zufluss', eur(f.zufluss));
      out('netto', eur(f.netto));

      if (f.zufluss > 0) {
        out('kern', 'Förderung: ' + eur(f.gesamt) + ' pro Jahr. Der Staat trägt ' +
          prozent(f.quote) + ' Ihrer Einzahlung.');
      } else {
        out('kern', 'Ohne Eigenbeitrag gibt es keine Förderung.');
      }

      var text;
      if (w.beitrag === 0) {
        text = 'Geben Sie einen Eigenbeitrag ein, um die Förderung zu sehen.';
      } else if (w.beitrag < MIN_EIGENBEITRAG) {
        text = 'Unter 120 EUR Eigenbeitrag im Jahr gibt es keine Zulagen. Es bleibt nur der Steuerabzug.';
      } else if (f.zusatz > 0) {
        text = 'Bei Ihnen gewinnt der Steuerabzug. Die Förderung entspricht Ihrer Steuerersparnis von ' +
          eur(f.entlastung) + '; die Zulagen sind darin enthalten, ' + eur(f.zusatz) +
          ' kommen mit dem Steuerbescheid hinzu.';
      } else {
        text = 'Bei Ihnen gewinnt die Zulage. Die Steuerersparnis aus dem Abzug (' + eur(f.entlastung) +
          ') liegt darunter, eine zusätzliche Erstattung gibt es nicht.';
      }
      if (w.kinder > 0 && w.beitrag >= MIN_EIGENBEITRAG && w.beitrag < KIND_MAX) {
        text += ' Mit 300 EUR Eigenbeitrag erreichen Sie die volle Kinderzulage.';
      }
      out('foerdertext', text);

      p.forEach(function (s, i) {
        out('kapital-' + i, zahl(s.kapital));
        out('steuer-' + i, zahl(s.steuer));
        out('avnetto-' + i, zahl(s.avNetto));
        out('frei-' + i, zahl(s.freiNetto));
        out('diff-' + i, zahlDiff(s.diff));
      });

      var mitte = p[1];
      var fazit;
      if (w.beitrag === 0) {
        fazit = '';
      } else if (Math.round(mitte.diff) >= 0) {
        fazit = 'Im mittleren Szenario liegt der geförderte Vertrag nach Steuern rund ' +
          eurRund(mitte.diff) + ' vor einem freien Depot mit demselben Nettoaufwand.';
      } else {
        fazit = 'Unter diesen Annahmen schneidet das freie Depot im mittleren Szenario um rund ' +
          eurRund(-mitte.diff) + ' besser ab: Die Förderung heute deckt die Steuer im Alter nicht.';
      }
      out('fazit', fazit);

      out('preistext', w.beitrag === 0 ? '' :
        'Ihr eigener Nettoaufwand über ' + w.jahre + ' Jahre: ' + eurRund(f.netto * w.jahre) +
        '. In heutiger Kaufkraft entspricht das Kapital im mittleren Szenario rund ' +
        eurRund(mitte.real) + '. Das Geld ist bis zur Auszahlung gebunden; wer vorher ' +
        'ohne begünstigten Zweck entnimmt, zahlt die Förderung zurück.');
    }

    root.querySelector('.bk-avd-form').addEventListener('submit', function (ev) { ev.preventDefault(); });
    root.addEventListener('input', rechnen);
    root.addEventListener('change', rechnen);
    rechnen();
  }

  window.bkAvd = { foerderung: foerderung, projektion: projektion, est: est };

  function start() {
    var roots = document.querySelectorAll('[data-bk-avd]');
    for (var i = 0; i < roots.length; i++) { init(roots[i]); }
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', start);
  } else {
    start();
  }
})();
