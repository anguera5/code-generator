export interface ModuleMeta {
  path: string
  title: string
  description?: string
}

export const modules: ModuleMeta[] = [
  {
    path: '/code-generator',
    title: 'Code Generator',
    description: 'Generate code, tests, and documentation using an LLM.'
  }
]
