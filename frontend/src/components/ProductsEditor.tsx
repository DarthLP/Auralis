import { useState } from 'react';

interface Product {
  name: string;
  category: string;
  short_desc: string;
}

interface ProductsEditorProps {
  products: Product[];
  onChange: (products: Product[]) => void;
  className?: string;
}

export default function ProductsEditor({ products, onChange, className = "" }: ProductsEditorProps) {
  const addProduct = () => {
    onChange([...products, { name: '', category: '', short_desc: '' }]);
  };

  const removeProduct = (index: number) => {
    onChange(products.filter((_, i) => i !== index));
  };

  const updateProduct = (index: number, field: keyof Product, value: string) => {
    const updated = [...products];
    updated[index] = { ...updated[index], [field]: value };
    onChange(updated);
  };

  return (
    <div className={`space-y-4 ${className}`}>
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-gray-900">Products</h3>
        <button
          type="button"
          onClick={addProduct}
          className="text-sm text-blue-600 hover:text-blue-800 font-medium"
        >
          + Add Product
        </button>
      </div>

      {products.length === 0 ? (
        <div className="text-center py-6 border-2 border-dashed border-gray-300 rounded-lg">
          <p className="text-gray-500 text-sm">No products added yet</p>
          <button
            type="button"
            onClick={addProduct}
            className="mt-2 text-blue-600 hover:text-blue-800 text-sm font-medium"
          >
            Add your first product
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          {products.map((product, index) => (
            <div key={index} className="p-4 border border-gray-200 rounded-lg bg-gray-50">
              <div className="flex items-start justify-between mb-3">
                <h4 className="text-sm font-medium text-gray-900">Product {index + 1}</h4>
                {products.length > 1 && (
                  <button
                    type="button"
                    onClick={() => removeProduct(index)}
                    className="text-red-600 hover:text-red-800 text-sm"
                  >
                    Remove
                  </button>
                )}
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1">
                    Name *
                  </label>
                  <input
                    type="text"
                    value={product.name}
                    onChange={(e) => updateProduct(index, 'name', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                    placeholder="Product name"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1">
                    Category
                  </label>
                  <input
                    type="text"
                    value={product.category}
                    onChange={(e) => updateProduct(index, 'category', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                    placeholder="e.g., SaaS, Hardware, etc."
                  />
                </div>
              </div>

              <div className="mt-3">
                <label className="block text-xs font-medium text-gray-700 mb-1">
                  Description
                </label>
                <textarea
                  value={product.short_desc}
                  onChange={(e) => updateProduct(index, 'short_desc', e.target.value)}
                  rows={2}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                  placeholder="Brief description of the product"
                />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
