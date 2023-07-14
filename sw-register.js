// main thread             we register our service worker here
// It's great to check for service worker support before registering our sw
if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register("serviceworker.js"); // To register the service worker, take in the url of the sw as its argument 
}
 