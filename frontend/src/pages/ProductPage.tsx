import { useParams } from 'react-router-dom'

export default function ProductPage() {
  const { companyId, productId } = useParams<{ companyId: string; productId: string }>()

  return (
    <div className="container">
      <h1 className="text-3xl font-bold text-gray-900 mb-6">Product: {productId}</h1>
      <p className="text-gray-600 mb-4">Company: {companyId}</p>
      <p className="text-gray-600">Product details and capabilities</p>
    </div>
  )
}
