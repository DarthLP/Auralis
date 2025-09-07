export type SpecValue =
  | { type: 'text'; value: string }
  | { type: 'number'; value: number; unit?: string }
  | { type: 'boolean'; value: boolean }
  | { type: 'enum'; value: string }
  | { type: 'range'; min: number; max: number; unit?: string }
  | { type: 'array'; value: SpecValue[] }
  | { type: 'url'; value: string };
