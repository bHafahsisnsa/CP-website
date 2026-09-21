// pages/admin/AdminCharactersPage.js — kelola taksonomi Character (facet MULTI storefront).
import React from 'react';
import AdminFacetPage from './AdminFacetPage';
import { listCharactersAdmin, createCharacter, updateCharacter, deleteCharacter } from '../../services/admin';
import { adminTestIds as T } from '../../constants/testIds/admin';

export default function AdminCharactersPage() {
  return (
    <AdminFacetPage
      title="Karakter"
      description="Karakter aroma (Fresh, Floral, Woody, …). Tampil di homepage & filter Shop."
      entityLabel="Karakter"
      service={{ list: listCharactersAdmin, create: createCharacter, update: updateCharacter, remove: deleteCharacter }}
      testIds={{ add: T.characterAdd, table: T.charactersTable, nameInput: 'admin-character-name', iconSelect: 'admin-character-icon', saveBtn: 'admin-character-save' }}
    />
  );
}
