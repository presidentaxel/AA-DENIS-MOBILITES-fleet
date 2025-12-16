import React from "react";
import { FiAward } from "react-icons/fi";

type TopUser = {
  no: number;
  driver: {
    id: string;
    first_name: string;
    last_name: string;
    email?: string;
  };
  earnings: number;
};

type TopUsersTableProps = {
  users: TopUser[];
  period: "week" | "month";
};

export function TopUsersTable({ users, period }: TopUsersTableProps) {
  const getInitials = (firstName: string, lastName: string): string => {
    const first = firstName?.charAt(0).toUpperCase() || "";
    const last = lastName?.charAt(0).toUpperCase() || "";
    return first + last;
  };

  return (
    <div className="top-users-table">
      <div className="top-users-table__header">
        <div className="top-users-table__title-section">
          <FiAward className="top-users-table__icon" />
          <h3 className="top-users-table__title">Top users</h3>
        </div>
        <select className="top-users-table__period-select">
          <option>{period === "week" ? "This Week" : "This Month"}</option>
        </select>
      </div>
      <div className="top-users-table__content">
        <table className="top-users-table__table">
          <thead>
            <tr>
              <th>No.</th>
              <th>Name</th>
              <th>Earnings</th>
            </tr>
          </thead>
          <tbody>
            {users.length === 0 ? (
              <tr>
                <td colSpan={3} className="top-users-table__empty">
                  No data available
                </td>
              </tr>
            ) : (
              users.map((user) => (
                <tr key={user.driver.id}>
                  <td className="top-users-table__no">{user.no}</td>
                  <td className="top-users-table__name">
                    <div className="top-users-table__avatar">
                      {getInitials(user.driver.first_name, user.driver.last_name)}
                    </div>
                    <div className="top-users-table__name-text">
                      <span className="top-users-table__name-initials">
                        {user.driver.first_name.charAt(0).toUpperCase()}
                        {user.driver.last_name.charAt(0).toUpperCase()}
                      </span>{" "}
                      {user.driver.first_name} {user.driver.last_name}
                    </div>
                  </td>
                  <td className="top-users-table__earnings">
                    {user.earnings.toFixed(2)} €
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

