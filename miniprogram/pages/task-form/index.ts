Page({
  data: {
    title: '',
    note: '',
    priority: 'medium'
  },
  onTitleInput(event: { detail: { value: string } }) {
    this.setData({ title: event.detail.value });
  },
  onNoteInput(event: { detail: { value: string } }) {
    this.setData({ note: event.detail.value });
  }
});
