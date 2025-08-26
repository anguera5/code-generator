import { defineStore } from 'pinia'

export type NotifyType = 'info' | 'success' | 'warning' | 'error'

export interface NotifyMessage {
  id: string
  type: NotifyType
  text: string
  timeout?: number
}

export const useNotifyStore = defineStore('notify', {
  state: () => ({
    queue: [] as NotifyMessage[],
    active: null as NotifyMessage | null,
    visible: false,
  }),
  actions: {
    show(type: NotifyType, text: string, timeout = 4000) {
      const msg: NotifyMessage = {
        id: `${Date.now()}-${Math.random().toString(36).slice(2)}`,
        type,
        text,
        timeout,
      }
      this.queue.push(msg)
      if (!this.active) this.next()
    },
    success(text: string, timeout?: number) {
      this.show('success', text, timeout)
    },
    info(text: string, timeout?: number) {
      this.show('info', text, timeout)
    },
    warning(text: string, timeout?: number) {
      this.show('warning', text, timeout)
    },
    error(text: string, timeout?: number) {
      this.show('error', text, timeout)
    },
    next() {
      if (this.active || this.queue.length === 0) return
      this.active = this.queue.shift() || null
      this.visible = !!this.active
    },
    close() {
      this.visible = false
    },
    onHidden() {
      this.active = null
      this.next()
    },
  },
})
