import React from 'react'
import { useParams } from 'react-router-dom'

export default function CompanyPage() {
  const { companyId } = useParams<{ companyId: string }>()

  return (
    <div>
      <h1>Company: {companyId}</h1>
    </div>
  )
}
