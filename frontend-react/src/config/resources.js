import { users } from '../api/users';
import { methodologies } from '../api/methodologies';
import { benefits } from '../api/benefits';
import { analysis } from '../api/analysis';

// Cada recurso describe su formulario y su tabla; CrudPage los dibuja
export const RESOURCES = {
  users: {
    title: 'Usuarios',
    api: users,
    createAsForm: true,
    fields: [
      { name: 'name', label: 'Nombre', type: 'text', required: true, max: 100 },
      { name: 'methodology_ids', label: 'Metodologías', type: 'multi', source: 'methodologies' },
      { name: 'img', label: 'Imagen (opcional)', type: 'file' },
    ],
    columns: [
      { key: 'img', label: 'Imagen', type: 'image' },
      { key: 'name', label: 'Nombre' },
      { key: 'methodology_ids', label: 'Metodologías', type: 'multi', source: 'methodologies' },
      { key: 'is_active', label: 'Estado', type: 'bool' },
    ],
  },
  methodologies: {
    title: 'Metodologías',
    api: methodologies,
    fields: [
      { name: 'name', label: 'Nombre', type: 'text', required: true, max: 100 },
      { name: 'description', label: 'Descripción', type: 'textarea', max: 500 },
      { name: 'benefit_ids', label: 'Beneficios', type: 'multi', source: 'benefits' },
    ],
    columns: [
      { key: 'name', label: 'Nombre' },
      { key: 'description', label: 'Descripción' },
      { key: 'benefit_ids', label: 'Beneficios', type: 'multi', source: 'benefits' },
      { key: 'is_active', label: 'Estado', type: 'bool' },
    ],
  },
  benefits: {
    title: 'Beneficios',
    api: benefits,
    fields: [
      { name: 'name', label: 'Nombre', type: 'text', required: true, max: 100 },
      { name: 'description', label: 'Descripción', type: 'textarea', max: 500 },
    ],
    columns: [
      { key: 'name', label: 'Nombre' },
      { key: 'description', label: 'Descripción' },
      { key: 'is_active', label: 'Estado', type: 'bool' },
    ],
  },
  analysis: {
    title: 'Análisis',
    api: analysis,
    fields: [
      { name: 'sector', label: 'Sector', type: 'text', required: true, max: 100 },
      { name: 'reach', label: 'Alcance (personas)', type: 'number', required: true, min: 0 },
      { name: 'time_in_social_media', label: 'Tiempo en redes (horas)', type: 'number', required: true, min: 0, step: 'any' },
      { name: 'user_id', label: 'Usuario', type: 'select', source: 'users', required: true, createOnly: true },
    ],
    columns: [
      { key: 'sector', label: 'Sector' },
      { key: 'reach', label: 'Alcance' },
      { key: 'time_in_social_media', label: 'Horas en redes' },
      { key: 'user_id', label: 'Usuario', type: 'ref', source: 'users' },
      { key: 'date', label: 'Fecha', type: 'date' },
      { key: 'is_active', label: 'Estado', type: 'bool' },
    ],
  },
};
