// ==UserScript==
// @name         Wisedu Cookie Sync
// @namespace    http://tampermonkey.net/
// @version      0.2
// @description  Syncs cookie to local service for automation tools. Now works with integrated client server.
// @author       You
// @match        http://emap.wisedu.com/*
// @grant        none
// ==/UserScript==

(function() {
    'use strict';

    function sendCookie() {
        const cookie = document.cookie;
        // 向本地运行的Python客户端（上传端或下载端）中集成的服务发送Cookie
        fetch('http://localhost:28570/set_cookie', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ cookie: cookie }),
        })
        .then(response => response.json())
        .then(data => console.log('Cookie Sync:', data.status))
        .catch(error => console.error('Cookie Sync Error:', error));
    }

    // 页面加载后，延迟一秒发送一次以确保获取最新Cookie
    setTimeout(sendCookie, 1000);

    // 每5分钟自动发送一次
    setInterval(sendCookie, 5 * 60 * 1000);
})();