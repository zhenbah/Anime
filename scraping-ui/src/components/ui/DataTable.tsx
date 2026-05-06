import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/Table';
import { cn } from '@/lib/utils';
import { useState } from 'react';
import { ArrowUpDown, ArrowUp, ArrowDown } from 'lucide-react';

interface Column<T> {
  key: keyof T | string;
  label: string;
  sortable?: boolean;
  render?: (item: T) => React.ReactNode;
}

interface DataTableProps<T> {
  data: T[];
  columns: Column<T>[];
  searchable?: boolean;
  searchKey?: keyof T;
  className?: string;
}

export function DataTable<T>({
  data,
  columns,
  searchable = true,
  searchKey,
  className,
}: DataTableProps<T>) {
  const [sortConfig, setSortConfig] = useState<{ key: string; direction: 'asc' | 'desc' } | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  const sortedData = React.useMemo(() => {
    if (!sortConfig) return data;
    return [...data].sort((a, b) => {
      const aValue = sortConfig.key.split('.').reduce((obj, key) => obj?.[key], a);
      const bValue = sortConfig.key.split('.').reduce((obj, key) => obj?.[key], b);
      
      if (aValue < bValue) return sortConfig.direction === 'asc' ? -1 : 1;
      if (aValue > bValue) return sortConfig.direction === 'asc' ? 1 : -1;
      return 0;
    });
  }, [data, sortConfig]);

  const filteredData = React.useMemo(() => {
    if (!searchQuery || !searchKey) return sortedData;
    return sortedData.filter(item => {
      const value = item[searchKey];
      return String(value).toLowerCase().includes(searchQuery.toLowerCase());
    });
  }, [sortedData, searchQuery, searchKey]);

  const handleSort = (key: string) => {
    setSortConfig(current => {
      if (!current || current.key !== key) {
        return { key, direction: 'asc' };
      }
      if (current.direction === 'asc') {
        return { key, direction: 'desc' };
      }
      return null;
    });
  };

  const getSortIcon = (key: string) => {
    if (!sortConfig || sortConfig.key !== key) {
      return <ArrowUpDown className="w-4 h-4 ml-1 opacity-50" />;
    }
    return sortConfig.direction === 'asc' 
      ? <ArrowUp className="w-4 h-4 ml-1" />
      : <ArrowDown className="w-4 h-4 ml-1" />;
  };

  return (
    <div className={cn('space-y-4', className)}>
      {searchable && searchKey && (
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search..."
            className="w-full pl-10 pr-4 py-2 bg-muted rounded-lg border border-border focus:border-primary focus:ring-1 focus:ring-primary transition-colors outline-none"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
      )}
      
      <div className="rounded-lg border border-border overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow>
              {columns.map((column) => (
                <TableHead
                  key={String(column.key)}
                  className={cn(
                    'font-semibold',
                    column.sortable && 'cursor-pointer select-none hover:text-primary transition-colors'
                  )}
                  onClick={() => column.sortable && handleSort(String(column.key))}
                >
                  <div className="flex items-center">
                    {column.label}
                    {column.sortable && getSortIcon(String(column.key))}
                  </div>
                </TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredData.map((item, index) => (
              <TableRow
                key={index}
                className="hover:bg-muted/50 transition-colors"
              >
                {columns.map((column) => (
                  <TableCell key={String(column.key)}>
                    {column.render
                      ? column.render(item)
                      : String(item[column.key as keyof T] ?? '')
                    }
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
