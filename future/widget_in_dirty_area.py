    # def widget_in_dirty_area(self, widget):
    #     """
    #     判断widget是否和dirty_area有重叠。
    #     """
    #     # 获取widget的边界
    #     x2_min, y2_min, width2, height2 = widget.dx, widget.dy, widget.width, widget.height

    #     for dirty_area in widget.parent.dirty_area_list:
    #         # 获取dirty_area的边界
    #         x1_min, y1_min, width1, height1 = dirty_area

    #         x1_max = x1_min + width1 - 1  # 脏区域的右边界
    #         y1_max = y1_min + height1 - 1 # 脏区域的上边界

    #         x2_max = x2_min + width2 - 1  # widget的右边界
    #         y2_max = y2_min + height2 - 1 # widget的上边界

    #         # 检查是否有交集
    #         if x1_min > x2_max or x2_min > x1_max:
    #             return False  # 在水平轴上没有交集
    #         if y1_min > y2_max or y2_min > y1_max:
    #             return False  # 在垂直轴上没有交集

    #         return True  # 存在交集