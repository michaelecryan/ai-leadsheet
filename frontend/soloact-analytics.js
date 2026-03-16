/**
 * soloact-analytics.js — Funnel event tracking helpers
 *
 * Fires events to GA4 (via GTM dataLayer), Meta Pixel (fbq), and TikTok Pixel (ttq).
 * All functions are no-ops if the respective pixel has not loaded.
 *
 * Usage:
 *   saTrack('upload_started')
 *   saTrack('signup_complete', { method: 'google' })
 *   saTrack('lesson_click', { chord: 'Am', provider: 'justinguitar' })
 */

function saTrack(eventName, params) {
  params = params || {};

  // ── GA4 via GTM dataLayer ──────────────────────────────────────────────────
  if (window.dataLayer) {
    window.dataLayer.push({ event: eventName, ...params });
  }

  // ── Meta Pixel ────────────────────────────────────────────────────────────
  if (typeof fbq === 'function') {
    // Map SoloAct events to Meta standard events where applicable
    const metaStandardMap = {
      signup_complete:          'CompleteRegistration',
      checkout_started:         'InitiateCheckout',
      subscription_activated:   'Purchase',
    };
    const metaEvent = metaStandardMap[eventName];
    if (metaEvent) {
      fbq('track', metaEvent, params);
    } else {
      fbq('trackCustom', eventName, params);
    }
  }

  // ── TikTok Pixel ──────────────────────────────────────────────────────────
  if (typeof ttq !== 'undefined' && typeof ttq.track === 'function') {
    const tiktokStandardMap = {
      signup_complete:          'CompleteRegistration',
      checkout_started:         'InitiateCheckout',
      subscription_activated:   'PlaceAnOrder',
    };
    const tiktokEvent = tiktokStandardMap[eventName];
    if (tiktokEvent) {
      ttq.track(tiktokEvent, params);
    } else {
      ttq.track(eventName, params);
    }
  }
}
