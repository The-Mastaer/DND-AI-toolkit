// supabase/functions/gemini-master-proxy/index.ts

import { serve } from 'https://deno.land/std@0.177.0/http/server.ts';
// Use the new SDK and its Content type definition
import { GoogleGenAI, Content } from 'https://esm.sh/@google/genai';

const GEMINI_API_KEY = Deno.env.get('GEMINI_API_KEY');

if (!GEMINI_API_KEY) {
  // Stop the server startup if the key is missing
  throw new Error("FATAL: GEMINI_API_KEY is not set in environment variables.");
}

// Initialize the client with the new object-based configuration.
const ai = new GoogleGenAI({ apiKey: GEMINI_API_KEY });

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

// Helper function to decode base64 string to a Uint8Array
function base64ToUint8Array(base64: string) {
  const binaryString = atob(base64);
  const len = binaryString.length;
  const bytes = new Uint8Array(len);
  for (let i = 0; i < len; i++) {
    bytes[i] = binaryString.charCodeAt(i);
  }
  return bytes;
}

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders });
  }

  try {
    const payload = await req.json();
    const {
      model,
      prompt,
      history,
      response_schema,
      file_uri,         // For referencing existing files (Rules Lawyer)
      file_mime_type,
      file_data_base64, // For uploading new files
      image_response,
      system_prompt     // For setting model behavior (Rules Lawyer)
    } = payload;

    if (!model || !prompt) {
        return new Response(JSON.stringify({ error: "Missing 'model' or 'prompt' in request body." }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' },
            status: 400
        });
    }

    // --- Image Generation Logic Path ---
    if (image_response === true) {
      const imageModel = "imagen-3.0-generate-002";
      console.log(`Received image generation request. Overriding model to: ${imageModel}`);

      const imageResult = await ai.models.generateImages({
        model: imageModel,
        prompt: prompt,
        config: { numberOfImages: 1 },
      });

      if (!imageResult.generatedImages || imageResult.generatedImages.length === 0) {
        console.error("Image generation failed. API Response:", imageResult);
        throw new Error("Image generation failed, no images were returned. This could be due to safety filters or an invalid prompt.");
      }

      const imageBytesBase64 = imageResult.generatedImages[0].image.imageBytes;
      const imageBytes = base64ToUint8Array(imageBytesBase64);

      return new Response(imageBytes, {
        headers: { ...corsHeaders, 'Content-Type': 'image/png' },
        status: 200,
      });
    }
    // --- END of Image Generation Logic ---


    // --- Text, Chat, and File Q&A Logic ---
    let generationConfig;
    if (response_schema) {
      generationConfig = {
        responseMimeType: "application/json",
        responseSchema: response_schema,
      };
    }

    const parts = [];

    // --- Handle file reference for Rules Lawyer ---
    if (file_uri && file_mime_type) {
      // --- FIX: Construct the full, valid Gemini File API URI ---
      const fullFileUri = `https://generativelanguage.googleapis.com/v1beta/${file_uri}`;
      console.log(`Attaching existing file for Q&A with full URI: ${fullFileUri}`);
      parts.push({
        fileData: {
          mimeType: file_mime_type,
          fileUri: fullFileUri // Use the constructed full URI
        }
      });
    }

    // Handle inline file data (if you need to upload and query in one go)
    if (file_data_base64 && file_mime_type && !file_uri) {
       parts.push({
        inlineData: {
          mimeType: file_mime_type,
          data: file_data_base64,
        },
      });
    }

    // Always add the main user prompt to the last part of the conversation
    parts.push({ text: prompt });

    // Construct the full conversation history.
    const contents: Content[] = history ? [...history, { role: 'user', parts }] : [{ role: 'user', parts }];

    const result = await ai.models.generateContent({
      model: model,
      contents: contents,
      config: generationConfig,
      systemInstruction: system_prompt ? { parts: [{ text: system_prompt }] } : undefined
    });

    return new Response(JSON.stringify(result), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      status: 200,
    });

  } catch (error) {
    console.error("Error in Gemini Proxy Edge Function:", error);
    return new Response(JSON.stringify({ error: error.message }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      status: 500,
    });
  }
});