// supabase/functions/gemini-master-proxy/index.ts

import { serve } from 'https://deno.land/std@0.177.0/http/server.ts';
// Import the official Google AI SDK using the import map
import { GoogleGenerativeAI, Part } from "@google/generative-ai";

// Get your API key from Supabase secrets
const GEMINI_API_KEY = Deno.env.get('GEMINI_API_KEY');

// Initialize the Google AI client with your API key
const genAI = new GoogleGenerativeAI(GEMINI_API_KEY!);

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type'
};

serve(async (req) => {
  // Handle CORS preflight request
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders });
  }

  try {
    const { model, prompt, response_schema, history, file_uri } = await req.json();

    // Get the specified generative model
    const generativeModel = genAI.getGenerativeModel({
      model: model,
      generationConfig: response_schema ? {
        responseMimeType: "application/json",
        responseSchema: response_schema
      } : undefined
    });

    const parts: Part[] = [];

    // If a file URI is provided, add it as a fileData part
    if (file_uri) {
      parts.push({
        fileData: {
          mimeType: 'application/pdf',
          uri: file_uri // The SDK uses 'uri' instead of 'file_uri'
        }
      });
    }

    // Add the text prompt
    parts.push({ text: prompt });

    // Generate content using the SDK
    const result = await generativeModel.generateContent({
        contents: [{ role: 'user', parts: parts }]
    });

    const response = result.response;

    // The SDK handles parsing, so we just return the response
    return new Response(JSON.stringify(response), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      status: 200
    });

  } catch (error) {
    return new Response(JSON.stringify({ error: error.message }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      status: 500
    });
  }
});