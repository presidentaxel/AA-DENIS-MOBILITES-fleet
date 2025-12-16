import React, { useState, useMemo } from "react";
import { RiArrowLeftSLine, RiArrowRightSLine } from "react-icons/ri";
import "../styles/date-range-picker.css";

type DateRangePickerProps = {
  dateFrom: string;
  dateTo: string;
  onApply: (from: string, to: string) => void;
  onClose: () => void;
};

type PresetOption = {
  label: string;
  getDates: () => { from: Date; to: Date };
};

export function DateRangePicker({ dateFrom, dateTo, onApply, onClose }: DateRangePickerProps) {
  const [selectedPreset, setSelectedPreset] = useState<string | null>(null);
  const [currentMonth, setCurrentMonth] = useState(new Date());
  const [selectedStartDate, setSelectedStartDate] = useState<Date | null>(
    dateFrom ? new Date(dateFrom) : null
  );
  const [selectedEndDate, setSelectedEndDate] = useState<Date | null>(
    dateTo ? new Date(dateTo) : null
  );
  const [isSelecting, setIsSelecting] = useState(false);

  const presetOptions: PresetOption[] = useMemo(
    () => [
      {
        label: "Current week",
        getDates: () => {
          const now = new Date();
          const dayOfWeek = now.getDay();
          const diff = now.getDate() - dayOfWeek + (dayOfWeek === 0 ? -6 : 1); // Monday
          const monday = new Date(now.getFullYear(), now.getMonth(), diff);
          monday.setHours(0, 0, 0, 0);
          const sunday = new Date(monday);
          sunday.setDate(monday.getDate() + 6);
          sunday.setHours(23, 59, 59, 999);
          return { from: monday, to: sunday };
        },
      },
      {
        label: "Last week",
        getDates: () => {
          const now = new Date();
          const dayOfWeek = now.getDay();
          const diff = now.getDate() - dayOfWeek + (dayOfWeek === 0 ? -6 : 1); // Monday
          const lastMonday = new Date(now.getFullYear(), now.getMonth(), diff - 7);
          lastMonday.setHours(0, 0, 0, 0);
          const lastSunday = new Date(lastMonday);
          lastSunday.setDate(lastMonday.getDate() + 6);
          lastSunday.setHours(23, 59, 59, 999);
          return { from: lastMonday, to: lastSunday };
        },
      },
      {
        label: "Last month",
        getDates: () => {
          const now = new Date();
          const firstDay = new Date(now.getFullYear(), now.getMonth() - 1, 1);
          const lastDay = new Date(now.getFullYear(), now.getMonth(), 0);
          lastDay.setHours(23, 59, 59, 999);
          return { from: firstDay, to: lastDay };
        },
      },
      {
        label: "Last 3 months",
        getDates: () => {
          const now = new Date();
          const threeMonthsAgo = new Date(now.getFullYear(), now.getMonth() - 3, 1);
          threeMonthsAgo.setHours(0, 0, 0, 0);
          return { from: threeMonthsAgo, to: now };
        },
      },
      {
        label: "Current Year",
        getDates: () => {
          const now = new Date();
          const firstDay = new Date(now.getFullYear(), 0, 1);
          firstDay.setHours(0, 0, 0, 0);
          return { from: firstDay, to: now };
        },
      },
      {
        label: "Last Year",
        getDates: () => {
          const now = new Date();
          const firstDay = new Date(now.getFullYear() - 1, 0, 1);
          firstDay.setHours(0, 0, 0, 0);
          const lastDay = new Date(now.getFullYear() - 1, 11, 31);
          lastDay.setHours(23, 59, 59, 999);
          return { from: firstDay, to: lastDay };
        },
      },
      {
        label: "Last + Current Year",
        getDates: () => {
          const now = new Date();
          const firstDay = new Date(now.getFullYear() - 1, 0, 1);
          firstDay.setHours(0, 0, 0, 0);
          return { from: firstDay, to: now };
        },
      },
      {
        label: "Last 2 Years",
        getDates: () => {
          const now = new Date();
          const twoYearsAgo = new Date(now.getFullYear() - 2, 0, 1);
          twoYearsAgo.setHours(0, 0, 0, 0);
          return { from: twoYearsAgo, to: now };
        },
      },
    ],
    []
  );

  const handlePresetClick = (preset: PresetOption, label: string) => {
    setSelectedPreset(label);
    const { from, to } = preset.getDates();
    setSelectedStartDate(from);
    setSelectedEndDate(to);
    setIsSelecting(false);
  };

  const handleDateClick = (date: Date) => {
    if (!selectedStartDate || (selectedStartDate && selectedEndDate)) {
      // Start new selection
      setSelectedStartDate(date);
      setSelectedEndDate(null);
      setIsSelecting(true);
    } else if (selectedStartDate && !selectedEndDate) {
      // Complete selection
      if (date < selectedStartDate) {
        setSelectedEndDate(selectedStartDate);
        setSelectedStartDate(date);
      } else {
        setSelectedEndDate(date);
      }
      setIsSelecting(false);
    }
  };

  // Helper function to format date as YYYY-MM-DD in local timezone
  const formatDateLocal = (date: Date): string => {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  };

  const handleApply = () => {
    if (selectedStartDate && selectedEndDate) {
      onApply(
        formatDateLocal(selectedStartDate),
        formatDateLocal(selectedEndDate)
      );
      onClose();
    }
  };

  const getDaysInMonth = (date: Date) => {
    return new Date(date.getFullYear(), date.getMonth() + 1, 0).getDate();
  };

  const getFirstDayOfMonth = (date: Date) => {
    return new Date(date.getFullYear(), date.getMonth(), 1).getDay();
  };

  const isDateInRange = (date: Date) => {
    if (!selectedStartDate || !selectedEndDate) return false;
    return date >= selectedStartDate && date <= selectedEndDate;
  };

  const isDateStart = (date: Date) => {
    if (!selectedStartDate) return false;
    return (
      date.getDate() === selectedStartDate.getDate() &&
      date.getMonth() === selectedStartDate.getMonth() &&
      date.getFullYear() === selectedStartDate.getFullYear()
    );
  };

  const isDateEnd = (date: Date) => {
    if (!selectedEndDate) return false;
    return (
      date.getDate() === selectedEndDate.getDate() &&
      date.getMonth() === selectedEndDate.getMonth() &&
      date.getFullYear() === selectedEndDate.getFullYear()
    );
  };

  const monthNames = [
    "janvier",
    "février",
    "mars",
    "avril",
    "mai",
    "juin",
    "juillet",
    "août",
    "septembre",
    "octobre",
    "novembre",
    "décembre",
  ];

  const dayNames = ["L", "M", "M", "J", "V", "S", "D"];

  const daysInMonth = getDaysInMonth(currentMonth);
  const firstDay = getFirstDayOfMonth(currentMonth);
  const days: (Date | null)[] = [];

  // Add empty cells for days before the first day of the month
  for (let i = 0; i < firstDay; i++) {
    days.push(null);
  }

  // Add all days of the month
  for (let day = 1; day <= daysInMonth; day++) {
    days.push(new Date(currentMonth.getFullYear(), currentMonth.getMonth(), day));
  }

  const prevMonth = () => {
    setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() - 1, 1));
  };

  const nextMonth = () => {
    setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1, 1));
  };

  return (
    <div className="date-range-picker-overlay" onClick={onClose}>
      <div className="date-range-picker" onClick={(e) => e.stopPropagation()}>
        <div className="date-range-picker__content">
          {/* Preset Options */}
          <div className="date-range-picker__presets">
            {presetOptions.map((preset) => (
              <button
                key={preset.label}
                className={`preset-button ${selectedPreset === preset.label ? "preset-button--active" : ""}`}
                onClick={() => handlePresetClick(preset, preset.label)}
              >
                {preset.label}
              </button>
            ))}
          </div>

          {/* Calendar */}
          <div className="date-range-picker__calendar">
            <div className="calendar-header">
              <button className="calendar-nav-button" onClick={prevMonth}>
                <RiArrowLeftSLine />
              </button>
              <h3 className="calendar-month-year">
                {monthNames[currentMonth.getMonth()]} {currentMonth.getFullYear()}
              </h3>
              <button className="calendar-nav-button" onClick={nextMonth}>
                <RiArrowRightSLine />
              </button>
            </div>

            <div className="calendar-weekdays">
              {dayNames.map((day, idx) => (
                <div key={idx} className="calendar-weekday">
                  {day}
                </div>
              ))}
            </div>

            <div className="calendar-days">
              {days.map((date, idx) => {
                if (!date) {
                  return <div key={`empty-${idx}`} className="calendar-day calendar-day--empty" />;
                }

                const inRange = isDateInRange(date);
                const isStart = isDateStart(date);
                const isEnd = isDateEnd(date);
                const isToday =
                  date.getDate() === new Date().getDate() &&
                  date.getMonth() === new Date().getMonth() &&
                  date.getFullYear() === new Date().getFullYear();

                return (
                  <div
                    key={date.toISOString()}
                    className={`calendar-day ${inRange ? "calendar-day--in-range" : ""} ${
                      isStart ? "calendar-day--start" : ""
                    } ${isEnd ? "calendar-day--end" : ""} ${isToday ? "calendar-day--today" : ""}`}
                    onClick={() => handleDateClick(date)}
                  >
                    {date.getDate()}
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="date-range-picker__footer">
          <button className="footer-button footer-button--close" onClick={onClose}>
            Close
          </button>
          <button
            className="footer-button footer-button--apply"
            onClick={handleApply}
            disabled={!selectedStartDate || !selectedEndDate}
          >
            Apply
          </button>
        </div>
      </div>
    </div>
  );
}

