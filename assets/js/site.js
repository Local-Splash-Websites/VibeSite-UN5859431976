(function () {
  document.documentElement.classList.add('js');

  var nav = document.getElementById('nav'), mb = document.querySelector('.menu-btn');
  mb.addEventListener('click', function () {
    var open = nav.classList.toggle('open');
    mb.setAttribute('aria-expanded', open);
  });
  document.querySelectorAll('.dd > button').forEach(function (b) {
    b.addEventListener('click', function () {
      var open = b.parentNode.classList.toggle('open');
      b.setAttribute('aria-expanded', open);
    });
  });
  nav.addEventListener('click', function (e) {
    if (e.target.tagName === 'A') { nav.classList.remove('open'); mb.setAttribute('aria-expanded', false); }
  });

  document.querySelectorAll('.day').forEach(function (d) {
    d.addEventListener('click', function () {
      document.querySelectorAll('.day').forEach(function (x) { x.setAttribute('aria-pressed', x === d); });
      document.querySelectorAll('form.form textarea[name=message]').forEach(function (t) {
        t.value = 'Preferred day: ' + d.textContent + '\n' + t.value.replace(/^Preferred day: \w+\n?/, '');
      });
    });
  });

  document.querySelectorAll('form.form').forEach(function (f) {
    var s1 = f.querySelector('[data-step="1"]'), s2 = f.querySelector('[data-step="2"]');
    var err = f.querySelector('.ferr'), ok = f.querySelector('.fok');
    function fail(msg, el) { err.textContent = msg; err.hidden = false; if (el) el.focus(); return false; }
    function step(n) { s1.classList.toggle('off', n === 2); s2.classList.toggle('on', n === 2); }
    function checkStep1() {
      var n = f.elements.name, p = f.elements.phone, m = f.elements.email;
      if (!n.value.trim()) return fail('Enter your name.', n);
      if (p.value.replace(/\D/g, '').length < 10) return fail('Enter a valid phone number, like +1 555-123-4567.', p);
      if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(m.value)) return fail('Enter an email address with @ and a domain.', m);
      err.hidden = true; return true;
    }
    f.querySelector('.next').addEventListener('click', function () {
      if (checkStep1()) { step(2); f.elements.service.focus(); }
    });
    f.querySelector('.back').addEventListener('click', function () { step(1); err.hidden = true; });
    f.addEventListener('submit', function (e) {
      e.preventDefault();
      if (!checkStep1()) { step(1); return; }
      if (!f.elements.consent.checked) return fail('Check the box to agree to the privacy policy before submitting.', f.elements.consent);
      err.hidden = true;
      var done = function () { s1.classList.add('off'); s2.classList.remove('on'); ok.hidden = false; };
      if (window.SITE_PREVIEW) return done();
      var btn = f.querySelector('[type=submit]');
      btn.disabled = true;
      fetch(f.action, { method: 'POST', body: new FormData(f), headers: { Accept: 'application/json' } })
        .then(function (r) { return r.json().then(function (j) { return { ok: r.ok && j.ok, j: j }; }); })
        .then(function (res) {
          btn.disabled = false;
          if (res.ok) done();
          else fail((res.j && res.j.error) || "That didn't work. The form wasn't sent. Please try again.");
        })
        .catch(function () { btn.disabled = false; fail("That didn't work. The form wasn't sent. Please try again or call us."); });
    });
  });
})();
