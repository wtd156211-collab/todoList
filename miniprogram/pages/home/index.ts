import type { FlowlistApp } from '../../app';
import { ensureSession } from '../../services/session';

Page({
  data: {
    greeting: '今天，专注完成一件重要的事。',
    tasks: [] as Array<{ id: string; title: string; dueText: string; priority: string }>,
    loadError: ''
  },
  async onShow() {
    const { stores } = getApp<FlowlistApp>().globalData;
    const session = await ensureSession(stores.session);
    if (!session.ok) {
      this.setData({ loadError: session.message });
      return;
    }

    await stores.tasks.refresh();
    this.setData({
      loadError: '',
      tasks: stores.tasks.items.map((task) => ({
        id: task.id,
        title: task.title,
        dueText: '',
        priority: task.priority
      }))
    });
  },
  onAddTask() {
    wx.navigateTo({ url: '/pages/task-form/index' });
  }
});
