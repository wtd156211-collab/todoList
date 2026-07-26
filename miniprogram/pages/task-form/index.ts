import { normalizeTaskDraft, validateTaskDraft } from '../../components/task-editor/index';
import type { FlowlistApp } from '../../app';
import { ensureSession } from '../../services/session';

Page({
  data: {
    title: '',
    note: '',
    priority: 'medium' as 'low' | 'medium' | 'high'
  },
  onTitleInput(event: { detail: { value: string } }) {
    this.setData({ title: event.detail.value });
  },
  onNoteInput(event: { detail: { value: string } }) {
    this.setData({ note: event.detail.value });
  },
  async onSave() {
    const draft = normalizeTaskDraft(this.data);
    const validationError = validateTaskDraft(draft);
    if (validationError) {
      wx.showToast({ title: validationError, icon: 'none' });
      return;
    }

    const { stores } = getApp<FlowlistApp>().globalData;
    const session = await ensureSession(stores.session);
    if (!session.ok) {
      wx.showToast({ title: session.message, icon: 'none' });
      return;
    }

    const result = await stores.tasks.create(draft);
    if (!result.ok) {
      wx.showToast({ title: result.message, icon: 'none' });
      return;
    }

    wx.showToast({ title: '任务已创建', icon: 'success' });
    wx.navigateBack();
  }
});
