import React, { useState } from 'react';
import { Mail, Phone, Briefcase, User } from 'lucide-react';

const UserProfileForm = () => {
  const [formData, setFormData] = useState({
    orgName: 'ABCD Organisation',
    email: 'bacd@gmail.com',
    phone: '9234934883',
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    // TODO: Replace with API call
    console.log('Saving user profile:', formData);
  };

  return (
    <div className='pl-14'>
    <form
      onSubmit={handleSubmit}
      className="bg-white p-6 rounded-xl  mb-4 mt-30 pt-5 shadow-md w-full max-w-sm"
    >
      <div className=" flex justify-center items-center">
        <h2 className="text-sm font-semibold text-gray-700 flex items-center">
          <span className="mr-1">▶</span> Personal details
        </h2>
      </div>

      <div className="flex justify-center mb-4">
        <div className="w-32 h-32 bg-gray-100 rounded-lg flex items-center justify-center">
          <User size={64} className="text-gray-500" />
        </div>
      </div>

      <div className="flex items-center bg-gray-100 rounded-lg px-3 py-2 mb-2">
        <Briefcase size={16} className="mr-2 text-gray-500" />
        <input
          type="text"
          name="orgName"
          value={formData.orgName}
          onChange={handleChange}
          placeholder="Organization"
          className="bg-transparent outline-none text-sm w-full"
        />
      </div>

      <div className="flex items-center bg-gray-100 rounded-lg px-3 py-2 mb-2">
        <Mail size={16} className="mr-2 text-gray-500" />
        <input
          type="email"
          name="email"
          value={formData.email}
          onChange={handleChange}
          placeholder="Email"
          className="bg-transparent outline-none text-sm w-full"
        />
      </div>

      <div className="flex items-center bg-gray-100 rounded-lg px-3 py-2 mb-4">
        <Phone size={16} className="mr-2 text-gray-500" />
        <input
          type="text"
          name="phone"
          value={formData.phone}
          onChange={handleChange}
          placeholder="Phone Number"
          className="bg-transparent outline-none text-sm w-full"
        />
      </div>

      <button
        type="submit"
        className="w-full bg-[#F29F67] text-white py-2 rounded-lg font-semibold hover:bg-[#e1874c] transition"
      >
        Save
      </button>

      {/* Theme Toggle Placeholder */}
      {/* 
        TODO: Implement theme toggle logic here
        You can use a checkbox or switch with Tailwind dark mode
      */}
    </form>
    </div>
  );
};

export default UserProfileForm;
