const CACHE_NAME = ‘anbeanews-v2’;
const urlsToCache = [’/’];

self.addEventListener(‘install’, function(event) {
event.waitUntil(
caches.open(CACHE_NAME).then(function(cache) {
return cache.addAll(urlsToCache);
})
);
});

self.addEventListener(‘fetch’, function(event) {
event.respondWith(
fetch(event.request).catch(function() {
return caches.match(event.request);
})
);
});

self.addEventListener(‘push’, function(event) {
const data = event.data ? event.data.json() : {};
const title = data.title || ‘Anbeanews’;
const options = {
body: data.body || ‘Yeni haber var!’,
icon: ‘/icon-192.png’,
badge: ‘/icon-192.png’,
data: { url: data.url || ‘/’ }
};
event.waitUntil(self.registration.showNotification(title, options));
});

self.addEventListener(‘notificationclick’, function(event) {
event.notification.close();
event.waitUntil(
clients.openWindow(event.notification.data.url || ‘/’)
);
});