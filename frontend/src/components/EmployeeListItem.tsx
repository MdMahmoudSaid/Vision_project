import type { FC } from 'react';

interface EmployeeListItemProps {
  id: string;
  fullName: string;
  employeeNumber: string;
  department?: string | null;
  active?: boolean;
  onSelect: (id: string, name: string) => void;
}

export const EmployeeListItem: FC<EmployeeListItemProps> = ({
  id,
  fullName,
  employeeNumber,
  department,
  active = true,
  onSelect
}) => {
  return (
    <button
      type="button"
      className={`badge-chip${active ? '' : ' is-inactive'}`}
      onClick={() => onSelect(id, fullName)}
      aria-label={`Sélectionner ${fullName}`}
    >
      <span className="badge-chip-id">{employeeNumber}</span>
      <span className="badge-chip-body">
        <span className="badge-chip-name">{fullName}</span>
        {department && <span className="badge-chip-meta"> · {department}</span>}
      </span>
    </button>
  );
};
