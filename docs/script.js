// Firebase configuration (replace with your actual Firebase credentials)
const firebaseConfig = {
    apiKey: "AIzaSyByNeUFYGFfjY5osqohMQfmKBzjezFuyGA",
    authDomain: "david-s-pico-box.firebaseapp.com",
    databaseURL: "https://david-s-pico-box-default-rtdb.firebaseio.com",
    projectId: "david-s-pico-box",
    storageBucket: "david-s-pico-box.firebasestorage.app",
    messagingSenderId: "961511409168",
    appId: "1:961511409168:web:72244a0d428384a1d5ac95"
  };

// Initialize Firebase
firebase.initializeApp(firebaseConfig);
const database = firebase.database();

// Handle form submission
document.getElementById("messageForm").addEventListener("submit", function(event) {
    event.preventDefault();

    // Get message from textarea
    const messageInput = document.getElementById("messageInput");
    const message = messageInput.value.trim();

    if (message) {
        // Push message to Firebase Realtime Database
        const messagesRef = database.ref("messages");
        messagesRef.push({
            text: message,
            timestamp: Date.now(),
            read: false
        }).then(() => {
            document.getElementById("status").textContent = "Message sent!";
            messageInput.value = ""; // Clear input
        }).catch((error) => {
            console.error("Error sending message:", error);
            document.getElementById("status").textContent = "Error sending message.";
        });
    }
});
