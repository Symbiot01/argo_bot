// // File: src/hooks/useChat.js
// 'use client';
// import { jwtDecode } from 'jwt-decode';
// import { useState } from 'react';

// export const useChat = (session) => {
//   const [messages, setMessages] = useState([]);
//   const [isThinking, setIsThinking] = useState(false);
//   const [chatId, setChatId] = useState(null);

//   // This is your defined fallback object.
//   const apiErrorFallback = {
//     sender: 'ai',
//     text: "The API is currently unavailable. Please try again later. This is a fallback message.",
//     imageUrl: null,
//   };

//   const processQueryWithPipeline = async (currentChatId, text) => {
//     try {
//       const response = await fetch('/api/chat/pipeline', {
//         method: 'POST',
//         headers: {
//           'Content-Type': 'application/json',
//           'Authorization': `Bearer ${session.accessToken}`,
//         },
//         body: JSON.stringify({
//           user_input: text,
//           chat_id: currentChatId,
//           user_id: jwtDecode(session.accessToken),
//           include_visualization: true,
//         }),
//       });

//       if (!response.ok) {
//         throw new Error(`Pipeline API Error: ${response.statusText}`);
//       }

//       const data = await response.json();
//       setMessages(prev => [
//         ...prev,
//         {
//           sender: 'ai',
//           text: data.response,
//           imageUrl: data.visualization_created ? data.visualization_url : null,
//         },
//       ]);
//     } catch (error) {
//       console.error("Failed to process pipeline query:", error);
//       // CORRECTED: Use the structured fallback object on failure.
//       setMessages(prev => [...prev, apiErrorFallback]);
//     }
//   };

//   const sendMessage = async (text) => {
//     setMessages(prev => [...prev, { sender: 'user', text }]);
//     setIsThinking(true);

//     try {
//       if (!chatId) {
//         // --- FIRST MESSAGE LOGIC ---

//         // 1. Get user data from sessionStorage
//         const storedSessionString = sessionStorage.getItem('user-session');
//         if (!storedSessionString) {
//           throw new Error("Session not found in storage. Please log in again.");
//         }
//         const storedSession = JSON.parse(storedSessionString);
//         const userId = storedSession.user.name; // Get the userid (username)
//         console.log("Creating new chat for user:", userId);
//         console.log(session.accessToken);
//         console.log(jwtDecode(session.accessToken));
//         console.log("New chat description:", text);

//         // 2. Create a new chat using the retrieved userid        
//         const newChatRes = await fetch('/api/chat/new', {
//           method: 'POST',
//           headers: {
//             'Content-Type': 'application/json',
//             'Authorization': `Bearer ${session.accessToken}`,
//           },
//           body: JSON.stringify({
//             userid: userId,
//             description: text,
//           }),
//         });
//         if(newChatRes.ok) console.log("New chat created successfully.");
//         if (!newChatRes.ok) throw new Error('Failed to create new chat.');

//         const newChatData = await newChatRes.json();
//         const newChatToken = newChatData.chat_token;
//         setChatId(newChatToken);
//         await processQueryWithPipeline(newChatToken, text);
//       } else {
//         await processQueryWithPipeline(chatId, text);
//       }
//     } catch (error) {
//       console.error("Failed to send message:", error);
//       // CORRECTED: Use the structured fallback object on failure.
//       setMessages(prev => [...prev, apiErrorFallback]);
//     } finally {
//       setIsThinking(false);
//     }
//   };

//   return { messages, isThinking, sendMessage };
// };

'use client';
import { useState } from 'react';

export const useChat = (session) => {
  const [messages, setMessages] = useState([]);
  const [isThinking, setIsThinking] = useState(false);
  // REMOVED: No longer need to track chatId state for now.
  // const [chatId, setChatId] = useState(null);

  const apiErrorFallback = {
    sender: 'ai',
    text: "The API is currently unavailable. Please try again later. This is a fallback message.",
    imageUrl: null,
  };

  const sendMessage = async (text) => {
    setMessages(prev => [...prev, { sender: 'user', text }]);
    setIsThinking(true);

    try {
      // CHANGED: We now call the pipeline directly on every message.
      const tempChatId = "temp-chat-session-123"; // A random placeholder chat ID
      const tempUserId = session.user.name;       // We can still use the actual user's name

      const response = await fetch('/api/chat/pipeline', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_input: text,
          chat_id: tempChatId, // Using the temporary ID // Using the temporary ID
          include_visualization: true,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        console.error("API Error Details:", errorData);
        throw new Error(`Pipeline API Error: ${response.statusText}`);
      }

      const data = await response.json();
      setMessages(prev => [
        ...prev,
        {
          sender: 'ai',
          text: data.response,
          imageUrl: data.visualization_created ? data.visualization_url : null,
        },
      ]);

    } catch (error) {
      console.error("Failed to send message:", error);
      setMessages(prev => [...prev, apiErrorFallback]);
    } finally {
      setIsThinking(false);
    }
  };

  return { messages, isThinking, sendMessage };
};