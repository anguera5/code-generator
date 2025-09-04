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
  ,{
    path: '/fpf-chatbot',
  title: 'Unofficial Food Packaging Forum Chatbot',
    description: 'Retrieval-augmented Q&A (prototype chatbot).'
  }
  ,{
    path: '/chembl-agent',
  title: 'ChEMBL Agent',
    description: 'Build schema index and query ChEMBL via RAG-generated SQL.'
  }
]
