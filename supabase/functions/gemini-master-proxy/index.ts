// supabase/functions/gemini-master-proxy/index.ts

import { serve } from 'https://deno.land/std@0.177.0/http/server.ts';
import {
  GoogleGenAI,
  Part,
  Content
} from "@google/genai";

const GEMINI_API_KEY = Deno.env.get('GEMINI_API_KEY');

// --- THIS IS THE FIX ---
// Initialize the client with the correct object structure, as you pointed out.
const genAI = new GoogleGenAI({ apiKey: GEMINI_API_KEY! });
// --- END OF FIX ---

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type'
};

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders });
  }

  try {
    const { model, prompt, response_schema, history, file_uri } = await req.json();

    const generativeModel = genAI.getGenerativeModel({
      model: model,
      generationConfig: response_schema ? {
        responseMimeType: "application/json",
        responseSchema: response_schema
      } : undefined
    });

    const parts: Part[] = [];

    // Manually create the file part object
    if (file_uri) {
      parts.push({
        fileData: {
          mimeType: 'application/pdf',
          fileUri: file_uri
        }
      });
    }

    parts.push({ text: prompt });

    const contents: Content[] = history ? [...history, { role: 'user', parts }] : [{ role: 'user', parts }];

    const result = await generativeModel.generateContent({ contents });
    const response = result.response;

    return new Response(JSON.stringify(response), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      status: 200
    });

  } catch (error) {
    console.error("Error in Edge Function:", error);
    return new Response(JSON.stringify({ error: error.message }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      status: 500
    });
  }
});