import * as XLSX from 'xlsx';

 const employees = [
    {
        empId: 'EMP001',
        name: 'Sahana',
        totalTests: 15,
        lastTestDate: '2024-01-20T10:30:00Z'
    },
    {
        empId: 'EMP002',
        name: 'Kavin',
        totalTests: 12,
        lastTestDate: '2024-01-22T16:20:00Z'
    },
    {
        empId: 'EMP003',
        name: 'Nandha',
        totalTests: 18,
        lastTestDate: '2024-01-21T12:45:00Z'
    },
    {
        empId: 'EMP004',
        name: 'Sajith',
        totalTests: 9,
        lastTestDate: '2024-01-23T09:15:00Z'
    },
    {
        empId: 'EMP005',
        name: 'Mithran',
        totalTests: 21,
        lastTestDate: '2024-01-24T11:30:00Z'
    }
];

const getTimeAgo = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInMs = now - date;
    const diffInDays = Math.floor(diffInMs / (1000 * 60 * 60 * 24));
    const diffInHours = Math.floor(diffInMs / (1000 * 60 * 60));

    if (diffInDays > 0) {
        return `${diffInDays} day${diffInDays > 1 ? 's' : ''} ago`;
    } else if (diffInHours > 0) {
        return `${diffInHours} hour${diffInHours > 1 ? 's' : ''} ago`;
    } else {
        return 'Less than 1 hour ago';
    }
};

export const exportToExcel = (employeeData = employees) => {
    const excelData = employeeData.map(emp => ({
        'Name': emp.name,
        'Employee ID': emp.empId,
        'Total Tests': emp.totalTests,
        'Last Test Date': new Date(emp.lastTestDate).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        }),
        'Time Ago': getTimeAgo(emp.lastTestDate)
    }));

    const worksheet = XLSX.utils.json_to_sheet(excelData);

    const columnWidths = [
        { wch: 15 },
        { wch: 12 },
        { wch: 12 },
        { wch: 15 },
        { wch: 18 }
    ];
    worksheet['!cols'] = columnWidths;

    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, 'Employee Test Data');

    const fileName = `Employee_Test_Data_${new Date().toISOString().split('T')[0]}.xlsx`;

    XLSX.writeFile(workbook, fileName);
};


// export const exportToExcel;


// const highPerformers = employees.filter(emp => emp.totalTests > 15);
// exportToExcel(highPerformers);

// const specificEmployee = employees.filter(emp => emp.name === 'Sahana');
// exportToExcel(specificEmployee);
