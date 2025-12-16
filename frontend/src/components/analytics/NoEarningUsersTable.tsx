import React from "react";
import { FiAlertTriangle } from "react-icons/fi";

type NoEarningUser = {
  no: number;
  driver: {
    id: string;
    first_name: string;
    last_name: string;
    email?: string;
  };
  earnings: number;
};

type NoEarningUsersTableProps = {
  users: NoEarningUser[];
  period: "week" | "month";
};

export function NoEarningUsersTable({ users, period }: NoEarningUsersTableProps) {
  const getInitials = (firstName: string, lastName: string): string => {
    const first = firstName?.charAt(0).toUpperCase() || "";
    const last = lastName?.charAt(0).toUpperCase() || "";
    return first + last;
  };

  return (
    <div className="no-earning-users-table">
      <div className="no-earning-users-table__header">
        <div className="no-earning-users-table__title-section">
          <FiAlertTriangle className="no-earning-users-table__icon" />
          <h3 className="no-earning-users-table__title">No earning users</h3>
        </div>
        <select className="no-earning-users-table__period-select">
          <option>{period === "week" ? "This Week" : "This Month"}</option>
        </select>
      </div>
      <div className="no-earning-users-table__content">
        <table className="no-earning-users-table__table">
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
                <td colSpan={3} className="no-earning-users-table__empty">
                  No data available
                </td>
              </tr>
            ) : (
              users.map((user) => (
                <tr key={user.driver.id}>
                  <td className="no-earning-users-table__no">{user.no}</td>
                  <td className="no-earning-users-table__name">
                    <div className="no-earning-users-table__avatar">
                      {getInitials(user.driver.first_name, user.driver.last_name)}
                    </div>
                    <div className="no-earning-users-table__name-text">
                      <span className="no-earning-users-table__name-initials">
                        {user.driver.first_name.charAt(0).toUpperCase()}
                        {user.driver.last_name.charAt(0).toUpperCase()}
                      </span>{" "}
                      {user.driver.first_name} {user.driver.last_name}
                    </div>
                  </td>
                  <td className="no-earning-users-table__earnings">
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

