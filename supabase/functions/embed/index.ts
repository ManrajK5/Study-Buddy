import 'jsr:@supabase/functions-js/edge-runtime.d.ts'

const model = new Supabase.ai.Session('gte-small')

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

Deno.serve(async (req: Request) => {
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  if (req.method !== 'POST') {
    return json({ error: 'Method not allowed' }, 405)
  }

  try {
    const body = await req.json()
    const input = body.input
    const inputs = body.inputs

    if (typeof input === 'string') {
      const embedding = await embed(input)
      return json({ embedding })
    }

    if (Array.isArray(inputs) && inputs.every((item) => typeof item === 'string')) {
      const embeddings = []
      for (const item of inputs) {
        embeddings.push(await embed(item))
      }
      return json({ embeddings })
    }

    return json({ error: 'Expected JSON body with input:string or inputs:string[].' }, 400)
  } catch (error) {
    return json({ error: error instanceof Error ? error.message : 'Unknown embedding error' }, 500)
  }
})

async function embed(input: string): Promise<number[]> {
  return await model.run(input, { mean_pool: true, normalize: true })
}

function json(payload: unknown, status = 200): Response {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { ...corsHeaders, 'Content-Type': 'application/json', Connection: 'keep-alive' },
  })
}
