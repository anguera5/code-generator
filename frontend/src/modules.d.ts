declare module './modules' {
  export interface ModuleMeta {
    path: string
    title: string
    description?: string
  }
  export const modules: ModuleMeta[]
}
