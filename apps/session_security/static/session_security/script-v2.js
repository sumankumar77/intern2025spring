// Use 'yourlabs' as namespace.
if (window.yourlabs === undefined) window.yourlabs = {};

// Session security constructor. These are the required options:
//
// - pingUrl: url to ping with last activity in this tab to get global last
//   activity time,
// - warnAfter: number of seconds of inactivity before warning,
// - expireAfter: number of seconds of inactivity before expiring the session.
//
// Optional options:
//
// - confirmFormDiscard: message that will be shown when the user tries to
//   leave a page with unsaved form data. Setting this will enable an
//   onbeforeunload handler that doesn't block expire().
// - events: a list of event types to watch for activity updates.
// - returnToUrl: a url to redirect users to expired sessions to. If this is not defined we just reload the page
yourlabs = (function () {
  'use strict';

  function SessionSecurity(options) {
    const t = this;
    // **HTML element** that should show to warn the user that his session will
    // expire.
    t.warning = document.getElementById('session_security_warning');

    // Last recorded activity datetime.
    t.lastActivity = new Date();

    // Events that would trigger an activity
    t.events = ['mousemove', 'scroll', 'keyup', 'click', 'touchstart', 'touchend', 'touchmove'];
    t.inputs = ['input', 'textarea', 'select', 'button'];
    t.options = options;

    // Bind activity events to update this.lastActivity.
    for (let i = 0; i < t.events.length; i++) {
      document.addEventListener(t.events[i], t.activity);
    }

    t.activity = function () {
      const now = new Date();
      if (now - t.lastActivity < 1000)
        // Throttle these checks to once per second
        return;

      const idleFor = Math.floor((now - t.lastActivity) / 1000);
      t.lastActivity = now;

      if (idleFor >= t.options.expireAfter) {
        // Enforces checking whether a user's session is expired. This
        // ensures a user being redirected instead of waiting until nextPing.
        t.expire();
      }

      if (t.isVisible(t.warning)) {
        // Inform the server that the user came back manually, this should
        // block other browser tabs from expiring.
        t.ping();
        // The hideWarning should only be called when the warning is visible
        t.hideWarning();
      }
    };

    t.ping = function () {
      const idleFor = Math.floor((new Date() - t.lastActivity) / 1000);
      const url = app.urlAddParams(t.options.pingUrl, {'idleFor': idleFor.toString()});

      fetch(url)
        .then(r => r.json())
        .then(response => {
          // handle the response
          t.pong(response);
        })
        .catch(error => {
          // handle the error
          t.apply();
        });
    };

    t.pong = function (data) {
      if (data === 'logout') return t.logout();
      if (data === 'expire') return t.expire();
      t.lastActivity = new Date();
      t.lastActivity.setSeconds(t.lastActivity.getSeconds() - data);
      t.apply();
    };


    // Initialize timers.
    t.apply();

    if (t.options.confirmFormDiscard) {
      //window.onbeforeunload = $.proxy(this.onbeforeunload, this);
      window.onbeforeunload = t.onbeforeunload;
      //$document.on('change', ':input', $.proxy(this.formChange, this));
      //$document.on('submit', 'form', $.proxy(this.formClean, this));
      //$document.on('reset', 'form', $.proxy(this.formClean, this));
      for (let i = 0; i < t.inputs.length; i++) {
        document.querySelectorAll(t.inputs[i]).forEach(el => {
          el.addEventListener('change', t.formChange);
        });
      }
      document.querySelectorAll('form').forEach(f => {
        f.addEventListener('submit', t.formClean);
        f.addEventListener('reset', t.formClean);
      });
    }

  }

  SessionSecurity.prototype.apply = function () {
    const t = this;
    // Cancel timeout if any, since we're going to make our own
    clearTimeout(t.timeout);

    const idleFor = Math.floor((new Date() - t.lastActivity) / 1000);

    let nextPing;
    if (idleFor >= t.options.expireAfter) {
      return this.expire();
    } else if (idleFor >= t.options.warnAfter) {
      //this.showWarning();
      nextPing = t.options.expireAfter - idleFor;
    } else {
      //this.hideWarning();
      nextPing = t.options.warnAfter - idleFor;
    }

    // setTimeout expects the timeout value not to exceed
    // a 32-bit unsigned int, so cap the value
    const milliseconds = Math.min(nextPing * 1000, 2147483647)
    t.timeout = setTimeout(t.ping, milliseconds);
  };

  SessionSecurity.prototype.logout = function () {
    this.expired = true;
    if (this.options.returnToUrl !== undefined) {
      window.location.href = this.options.returnToUrl;
    } else {
      window.location.reload();
    }
  };

  SessionSecurity.prototype.expire = function () {
    this.expired = true;
  };

  // Called when there has been no activity for more than warnAfter
  // seconds.
  SessionSecurity.prototype.showWarning = function () {
    app.fadeIn(this.warning);
    this.warning.setAttribute('aria-hidden', 'false');
    document.querySelector('.session_security_modal').focus();
  };

  // Called to hide the warning, for example if there has been activity on
  // the server side - in another browser tab.
  SessionSecurity.prototype.hideWarning = function () {
    this.warning.style.display = 'none';
    this.warning.setAttribute('aria-hidden', 'true');
  };

  SessionSecurity.prototype.isVisible = function (el) {
    return el.style.display !== 'none';
  };

  // Callback to process PingView response.
  SessionSecurity.prototype.pong = function (data) {
    if (data === 'logout') return this.logout();
    if (data === 'expire') return this.expire();
    this.lastActivity = new Date();
    this.lastActivity.setSeconds(this.lastActivity.getSeconds() - data);
    this.apply();
  };

  // onbeforeunload handler.
  SessionSecurity.prototype.onbeforeunload = function (e) {
    if (!!document.querySelector('form[data-dirty]') && !this.expired) {
      return this.options.confirmFormDiscard;
    }
  };

  // When an input change, set data-dirty attribute on its form.
  SessionSecurity.prototype.formChange = function (e) {
    e.target.closest('form').setAttribute('data-dirty', true);
  };

  // When a form is submitted or resetted, unset data-dirty attribute.
  SessionSecurity.prototype.formClean = function (e) {
    e.target.removeAttribute('data-dirty');
  };

  return {SessionSecurity};

}());