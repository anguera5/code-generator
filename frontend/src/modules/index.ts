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
  },
  {
    path: '/code-review',
    title: 'Code Review',
    description: 'LLM-assisted pull request review via repository webhook.'
  }
]
