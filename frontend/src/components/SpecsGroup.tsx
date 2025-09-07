import { Product } from '@schema/types';
import { SpecValue } from '@schema/specs';

interface SpecProfile {
  id: string;
  name: string;
  version: string;
  schema: Record<string, {
    type: string;
    unit?: string;
    label?: string;
  }>;
  ui?: {
    groups: Array<{
      name: string;
      fields: string[];
    }>;
  };
}

interface SpecsGroupProps {
  product: Product;
  profile?: SpecProfile;
}

// Render individual spec values based on their type
function renderSpecValue(spec: SpecValue): React.ReactNode {
  switch (spec.type) {
    case 'number':
      return (
        <span className="text-gray-900">
          {spec.value}
          {spec.unit && <span className="text-gray-500 ml-1">{spec.unit}</span>}
        </span>
      );
    
    case 'range':
      return (
        <span className="text-gray-900">
          {spec.min}–{spec.max}
          {spec.unit && <span className="text-gray-500 ml-1">{spec.unit}</span>}
        </span>
      );
    
    case 'text':
      return <span className="text-gray-900">{spec.value}</span>;
    
    case 'boolean':
      return (
        <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
          spec.value ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
        }`}>
          {spec.value ? 'Yes' : 'No'}
        </span>
      );
    
    case 'enum':
      return (
        <span className="inline-flex items-center px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full">
          {spec.value}
        </span>
      );
    
    case 'url':
      return (
        <a
          href={spec.value}
          target="_blank"
          rel="noopener noreferrer"
          className="text-blue-600 hover:text-blue-800 underline"
        >
          {spec.value}
        </a>
      );
    
    case 'array':
      return (
        <ul className="list-disc list-inside space-y-1">
          {spec.value.map((item: SpecValue, index: number) => (
            <li key={index} className="text-gray-900">
              {renderSpecValue(item)}
            </li>
          ))}
        </ul>
      );
    
    default:
      return <span className="text-gray-500 italic">Unknown type</span>;
  }
}

// Get field label from profile or use field name
function getFieldLabel(fieldName: string, profile?: SpecProfile): string {
  if (profile?.schema[fieldName]?.label) {
    return profile.schema[fieldName].label;
  }
  // Convert camelCase to Title Case
  return fieldName.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase());
}

export default function SpecsGroup({ product, profile }: SpecsGroupProps) {
  if (!product.specs || Object.keys(product.specs).length === 0) {
    return (
      <div className="bg-gray-50 rounded-lg p-8 text-center">
        <p className="text-gray-500 text-lg">No specifications available.</p>
      </div>
    );
  }

  const specs = product.specs;
  const specKeys = Object.keys(specs);

  // If profile has UI groups, use them; otherwise create a simple structure
  let groups: Array<{ name: string; fields: string[] }>;
  let unknownFields: string[] = [];

  if (profile?.ui?.groups) {
    // Use profile-defined groups
    groups = profile.ui.groups;
    
    // Find fields not in any group
    const definedFields = new Set(profile.ui.groups.flatMap(group => group.fields));
    unknownFields = specKeys.filter(key => !definedFields.has(key));
  } else {
    // Simple key/value table - all specs in one group
    groups = [{ name: 'Specifications', fields: specKeys }];
  }

  return (
    <div className="space-y-6">
      {groups.map((group, groupIndex) => (
        <div key={groupIndex} className="bg-white rounded-lg border border-gray-200">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">{group.name}</h3>
          </div>
          <div className="px-6 py-4">
            <dl className="space-y-4">
              {group.fields.map((fieldName) => {
                const spec = specs[fieldName];
                if (!spec) return null;
                
                return (
                  <div key={fieldName} className="flex flex-col sm:flex-row sm:items-start">
                    <dt className="text-sm font-medium text-gray-600 sm:w-1/3 sm:flex-shrink-0">
                      {getFieldLabel(fieldName, profile)}
                    </dt>
                    <dd className="mt-1 text-sm sm:mt-0 sm:ml-6 sm:w-2/3">
                      {renderSpecValue(spec)}
                    </dd>
                  </div>
                );
              })}
            </dl>
          </div>
        </div>
      ))}

      {/* Unknown fields group */}
      {unknownFields.length > 0 && (
        <div className="bg-yellow-50 rounded-lg border border-yellow-200">
          <div className="px-6 py-4 border-b border-yellow-200">
            <div className="flex items-center">
              <h3 className="text-lg font-semibold text-gray-900">Other</h3>
              <span className="ml-2 inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                Unknown fields
              </span>
            </div>
          </div>
          <div className="px-6 py-4">
            <dl className="space-y-4">
              {unknownFields.map((fieldName) => {
                const spec = specs[fieldName];
                if (!spec) return null;
                
                return (
                  <div key={fieldName} className="flex flex-col sm:flex-row sm:items-start">
                    <dt className="text-sm font-medium text-gray-600 sm:w-1/3 sm:flex-shrink-0">
                      {getFieldLabel(fieldName, profile)}
                    </dt>
                    <dd className="mt-1 text-sm sm:mt-0 sm:ml-6 sm:w-2/3">
                      {renderSpecValue(spec)}
                    </dd>
                  </div>
                );
              })}
            </dl>
          </div>
        </div>
      )}
    </div>
  );
}
