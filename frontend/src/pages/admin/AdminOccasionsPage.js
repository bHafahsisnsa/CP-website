// pages/admin/AdminOccasionsPage.js — kelola taksonomi Occasion (facet MULTI storefront).
import React from 'react';
import AdminFacetPage from './AdminFacetPage';
import { listOccasions, createOccasion, updateOccasion, deleteOccasion } from '../../services/admin';
import { adminTestIds as T } from '../../constants/testIds/admin';

export default function AdminOccasionsPage() {
  return (
    <AdminFacetPage
      title="Occasion"
      description="Momen pemakaian (Office, Gym, Date Night, …). Tampil di homepage & filter Shop."
      entityLabel="Occasion"
      service={{ list: listOccasions, create: createOccasion, update: updateOccasion, remove: deleteOccasion }}
      testIds={{ add: T.occasionAdd, table: T.occasionsTable, nameInput: 'admin-occasion-name', iconSelect: 'admin-occasion-icon', saveBtn: 'admin-occasion-save' }}
    />
  );
}
