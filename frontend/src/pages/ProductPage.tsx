import React from 'react'
import { useParams } from 'react-router-dom'

export default function ProductPage() {
  const { companyId, productId } = useParams<{ companyId: string; productId: string }>()

  return (
    <div>
      <h1>Product: {productId}</h1>
      <p>Company: {companyId}</p>
    </div>
  )
}
