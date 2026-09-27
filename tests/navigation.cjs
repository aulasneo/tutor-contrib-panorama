// Install dependencies with npm ci; run the full generated-config check with make test-navigation.
const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { JSDOM } = require('jsdom');
const dom = new JSDOM('<html><body></body></html>', { url: 'https://apps.example.org' });
global.window = dom.window;
global.document = dom.window.document;
Object.defineProperty(global, 'navigator', { value: dom.window.navigator, configurable: true });
global.IS_REACT_ACT_ENVIRONMENT = true;
const React = require('react');
const { render, act, cleanup } = require('@testing-library/react');
const babel = require('@babel/core');
const patches = path.join(__dirname, '../tutorpanorama/patches');

for (const native of [false, true]) {
  test(`${native ? 'native' : 'legacy'} navigation follows backend grants and authentication changes`, async () => {
    let user = null;
    let change;
    let unsubscribed = 0;
    let pending = [];
    const client = { get: (url) => {
      assert.equal(url, 'https://lms.example.org/panorama/api/get-user-access');
      return new Promise((resolve, reject) => pending.push({ resolve, reject }));
    } };
    const file = native ? 'mfe-site-custom-app-final' : 'mfe-env-config-buildtime-definitions';
    let source = fs.readFileSync(path.join(patches, file), 'utf8').replace(/{%.*?%}/g, '');
    source = babel.transformSync(source, { filename: 'navigation.ts', configFile: false, babelrc: false,
      plugins: [require.resolve('@babel/plugin-transform-typescript')] }).code;
    const bindings = native ? {
      panoramaSiteCreateElement: React.createElement, panoramaSiteUseEffect: React.useEffect,
      panoramaSiteUseState: React.useState, panoramaSiteUseUser: () => user,
      panoramaSiteUseConfig: () => ({ lmsBaseUrl: 'https://lms.example.org', commonAppConfig: { PANORAMA_URL: '/panorama/' } }),
      panoramaSiteHttpClient: () => client,
    } : {
      panoramaCreateElement: React.createElement, panoramaUseEffect: React.useEffect, panoramaUseState: React.useState,
      panoramaGetAuthenticatedUser: () => user,
      panoramaGetConfig: () => ({ LMS_BASE_URL: 'https://lms.example.org', PANORAMA_URL: '/panorama/' }),
      panoramaGetAuthenticatedHttpClient: () => client, PANORAMA_AUTH_CHANGED: 'changed',
      panoramaSubscribe: (_topic, callback) => { change = callback; return 'subscription'; },
      panoramaUnsubscribe: token => { assert.equal(token, 'subscription'); unsubscribed += 1; },
    };
    const Component = new Function(...Object.keys(bindings), `${source}; return ${native ? 'PanoramaSiteLink' : 'PanoramaNavigationLink'};`)(...Object.values(bindings));
    const view = render(React.createElement(Component));
    const switchUser = async next => act(async () => {
      user = next;
      if (native) view.rerender(React.createElement(Component)); else change();
    });
    assert.equal(view.queryByRole('link'), null);
    assert.equal(pending.length, 0);
    await switchUser({ username: 'granted-reader', administrator: false });
    await act(async () => pending.shift().resolve({ data: { body: true } }));
    assert.equal(view.getByRole('link').getAttribute('href'), '/panorama/');
    await switchUser({ username: 'administrator-without-grant', administrator: true });
    assert.equal(view.queryByRole('link'), null);
    await act(async () => pending.shift().resolve({ data: { body: false } }));
    assert.equal(view.queryByRole('link'), null);
    await switchUser({ username: 'expired-session' });
    await act(async () => pending.shift().reject(new Error('401')));
    assert.equal(view.queryByRole('link'), null);
    await switchUser({ username: 'pending' });
    await switchUser(null);
    await act(async () => pending.shift().resolve({ data: { body: true } }));
    assert.equal(view.queryByRole('link'), null);
    cleanup();
    if (!native) assert.equal(unsubscribed, 1);
  });
}

test('generated combined imports have no duplicate local bindings', {
  skip: !process.env.PANORAMA_GENERATED_ENV && 'Set PANORAMA_GENERATED_ENV to a Tutor-generated env.config.jsx',
}, () => {
  babel.parseSync(fs.readFileSync(process.env.PANORAMA_GENERATED_ENV, 'utf8'), {
    configFile: false, babelrc: false, parserOpts: { sourceType: 'module', plugins: ['jsx'] },
  });
});


test('generated frontend-base configuration has no duplicate local bindings', {
  skip: !process.env.PANORAMA_GENERATED_ENV && 'Set PANORAMA_GENERATED_ENV to a Tutor-generated env.config.jsx',
}, () => {
  const site = path.join(path.dirname(process.env.PANORAMA_GENERATED_ENV), 'site');
  for (const filename of ['src/customApp.tsx', 'site.config.build.tsx']) {
    babel.parseSync(fs.readFileSync(path.join(site, filename), 'utf8'), {
      configFile: false, babelrc: false,
      parserOpts: { sourceType: 'module', plugins: ['jsx', 'typescript'] },
    });
  }
});
