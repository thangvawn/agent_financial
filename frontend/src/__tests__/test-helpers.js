import { createServer } from 'vite'
import React from 'react'
import { renderToString } from 'react-dom/server'

let viteServer = null

export async function getViteServer() {
  if (!viteServer) {
    viteServer = await createServer({
      server: { middlewareMode: true },
      appType: 'custom',
    })
  }
  return viteServer
}

export async function loadComponent(componentRelativePath) {
  const server = await getViteServer()
  const mod = await server.ssrLoadModule(componentRelativePath)
  return mod.default || mod
}

export async function closeViteServer() {
  if (viteServer) {
    await viteServer.close()
    viteServer = null
  }
}

export { React, renderToString }
