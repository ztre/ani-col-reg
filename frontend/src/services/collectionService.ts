import type { CollectionItem } from '../types'

import { request } from './http'

export function saveCollection(payload: Partial<CollectionItem> & { anime_id: number }): Promise<CollectionItem> {
  return request<CollectionItem>('/api/collection', {
    method: 'POST',
    body: JSON.stringify(payload)
  })
}

export function updateCollection(id: number, payload: Partial<CollectionItem>): Promise<CollectionItem> {
  return request<CollectionItem>(`/api/collection/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(payload)
  })
}

export function deleteCollection(id: number): Promise<CollectionItem> {
  return request<CollectionItem>(`/api/collection/${id}`, {
    method: 'DELETE'
  })
}